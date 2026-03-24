# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('actividades_complementarias', '-standard')
class TestActividad(TransactionCase):
    """Tests para el modelo actividad.complementaria.

    Los registros de catálogo (estados, periodos) se obtienen con env.ref().
    No se crean duplicados en los tests.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.estado_aprobada = cls.env.ref('actividades_complementarias.estado_aprobada')
        cls.estado_rechazada = cls.env.ref('actividades_complementarias.estado_rechazada')
        cls.estado_pendiente = cls.env.ref('actividades_complementarias.estado_pendiente_inicio')
        cls.estado_en_curso = cls.env.ref('actividades_complementarias.estado_en_curso')
        cls.estado_finalizada = cls.env.ref('actividades_complementarias.estado_finalizada')

        cls.periodo = cls.env.ref('actividades_complementarias.periodo_2025_A')
        cls.periodo_b = cls.env.ref('actividades_complementarias.periodo_2025_B')

        cls.tipo = cls.env['actividad.tipo'].create({'name': 'Conferencia Test'})

        cls.manana = date.today() + timedelta(days=1)
        cls.pasado_manana = date.today() + timedelta(days=2)

        # Usuario de prueba para responsable (no requiere grupo específico para tests unitarios)
        cls.user_responsable = cls.env['res.users'].create({
            'name': 'Responsable Test',
            'login': 'resp_test_actividad@test.local',
        })

    def _make_actividad(self, **kwargs):
        """Helper: crea una actividad con valores mínimos válidos.

        Usa skip_fecha_check para evitar que el constraint de fecha_inicio
        bloquee tests que necesitan fechas pasadas.
        """
        vals = {
            'name': 'Actividad de prueba',
            'tipo_actividad_id': self.tipo.id,
            'periodo': self.periodo.id,
            'fecha_inicio': self.manana,
            'fecha_fin': self.pasado_manana,
            'cantidad_horas': 8.0,
            'cupo_min': 5,
            'cupo_max': 30,
        }
        vals.update(kwargs)
        return self.env['actividad.complementaria'].create(vals)

    # ── Constraints de fechas ────────────────────────────────────────────────

    def test_fecha_inicio_pasada_falla(self):
        """No se debe poder crear una actividad con fecha de inicio en el pasado."""
        with self.assertRaises(ValidationError):
            self.env['actividad.complementaria'].create({
                'name': 'Actividad pasada',
                'tipo_actividad_id': self.tipo.id,
                'periodo': self.periodo.id,
                'fecha_inicio': date.today() - timedelta(days=1),
                'fecha_fin': date.today() + timedelta(days=1),
                'cantidad_horas': 4.0,
            })

    def test_fecha_fin_antes_de_inicio_falla(self):
        """La fecha de fin debe ser posterior a la fecha de inicio."""
        with self.assertRaises(ValidationError):
            self._make_actividad(fecha_inicio=self.manana, fecha_fin=self.manana)

    # ── Constraints de cupos ─────────────────────────────────────────────────

    def test_cupo_min_cero_falla(self):
        """El cupo mínimo debe ser al menos 1."""
        with self.assertRaises(ValidationError):
            self._make_actividad(cupo_min=0)

    def test_cupo_max_menor_que_min_falla(self):
        """El cupo máximo no puede ser menor que el mínimo."""
        with self.assertRaises(ValidationError):
            self._make_actividad(cupo_min=10, cupo_max=5)

    def test_cupo_ilimitado_omite_validacion_cupos(self):
        """Con cupo_ilimitado=True no se validan min/max."""
        actividad = self._make_actividad(cupo_ilimitado=True, cupo_min=0, cupo_max=0)
        self.assertTrue(actividad.cupo_ilimitado)

    # ── Constraint de nombre único por periodo ───────────────────────────────

    def test_nombre_duplicado_mismo_periodo_falla(self):
        """No puede haber dos actividades activas con el mismo nombre en el mismo periodo."""
        self._make_actividad(name='Actividad Única', estado_id=self.estado_aprobada.id)
        with self.assertRaises(ValidationError):
            self._make_actividad(name='Actividad Única', estado_id=self.estado_aprobada.id)

    def test_nombre_duplicado_diferente_periodo_ok(self):
        """El mismo nombre en diferente periodo sí es válido."""
        self._make_actividad(name='Actividad Repetida', periodo=self.periodo.id)
        actividad2 = self._make_actividad(name='Actividad Repetida', periodo=self.periodo_b.id)
        self.assertTrue(actividad2.id)

    def test_nombre_duplicado_estado_rechazada_ok(self):
        """Se permite el mismo nombre si la actividad anterior fue rechazada."""
        self._make_actividad(name='Actividad Reciclada', estado_id=self.estado_rechazada.id)
        actividad2 = self._make_actividad(name='Actividad Reciclada', estado_id=self.estado_aprobada.id)
        self.assertTrue(actividad2.id)

    # ── Business logic: action_enviar_catalogo ───────────────────────────────

    def test_enviar_catalogo_sin_estado_aprobado_falla(self):
        """No se puede enviar al catálogo una actividad sin estado aprobado."""
        actividad = self._make_actividad()
        with self.assertRaises(ValidationError):
            actividad.action_enviar_catalogo()

    def test_enviar_catalogo_rechazada_falla(self):
        """Una actividad rechazada no puede enviarse al catálogo."""
        actividad = self._make_actividad(estado_id=self.estado_rechazada.id)
        with self.assertRaises(ValidationError):
            actividad.action_enviar_catalogo()

    def test_enviar_catalogo_finalizada_falla(self):
        """Una actividad finalizada no puede enviarse al catálogo."""
        actividad = self._make_actividad(estado_id=self.estado_finalizada.id)
        with self.assertRaises(ValidationError):
            actividad.action_enviar_catalogo()

    def test_enviar_catalogo_aprobada_ok(self):
        """Una actividad aprobada puede enviarse al catálogo."""
        actividad = self._make_actividad(estado_id=self.estado_aprobada.id)
        actividad.action_enviar_catalogo()
        self.assertTrue(actividad.en_catalogo)

    def test_enviar_catalogo_pendiente_inicio_ok(self):
        """Una actividad pendiente de inicio puede enviarse al catálogo."""
        actividad = self._make_actividad(estado_id=self.estado_pendiente.id)
        actividad.action_enviar_catalogo()
        self.assertTrue(actividad.en_catalogo)

    # ── Business logic: firma dual de constancias ────────────────────────────

    def test_firmar_constancias_requiere_finalizada(self):
        """No se pueden firmar constancias de una actividad no finalizada."""
        actividad = self._make_actividad(estado_id=self.estado_aprobada.id)
        with self.assertRaises(ValidationError):
            actividad.action_firmar_constancias()

    def test_firmar_constancias_jd_ok(self):
        """El JD puede firmar su parte en una actividad finalizada."""
        actividad = self._make_actividad(estado_id=self.estado_finalizada.id)
        actividad.action_firmar_constancias()
        self.assertTrue(actividad.jd_firmo)

    def test_constancias_firmadas_requiere_ambas_firmas(self):
        """constancias_firmadas es False con solo la firma del JD."""
        actividad = self._make_actividad(estado_id=self.estado_finalizada.id)
        actividad.action_firmar_constancias()
        self.assertTrue(actividad.jd_firmo)
        self.assertFalse(actividad.responsable_firmo)
        self.assertFalse(actividad.constancias_firmadas)

    def test_constancias_firmadas_true_con_ambas_firmas(self):
        """constancias_firmadas es True solo cuando ambas partes firmaron."""
        actividad = self._make_actividad(estado_id=self.estado_finalizada.id)
        actividad.action_firmar_constancias()
        actividad.write({'responsable_firmo': True})
        self.assertTrue(actividad.constancias_firmadas)

    def test_jd_no_puede_firmar_dos_veces(self):
        """El JD no puede firmar las constancias más de una vez."""
        actividad = self._make_actividad(estado_id=self.estado_finalizada.id)
        actividad.action_firmar_constancias()
        with self.assertRaises(ValidationError):
            actividad.action_firmar_constancias()

    # ── Selección de créditos ────────────────────────────────────────────────

    def test_creditos_valores_validos(self):
        """Los cuatro valores de créditos válidos deben poder asignarse."""
        for valor in ('0.5', '1.0', '1.5', '2.0'):
            act = self._make_actividad(
                name=f'Actividad créditos {valor}',
                creditos=valor,
                estado_id=self.estado_aprobada.id,
            )
            self.assertEqual(act.creditos, valor)

    # ── Computes ─────────────────────────────────────────────────────────────

    def test_alumno_count_compute(self):
        """El contador de alumnos debe reflejar los registros en Many2many."""
        actividad = self._make_actividad()
        self.assertEqual(actividad.alumno_count, 0)

        user1 = self.env['res.users'].create({
            'name': 'Alumno Count Test 1',
            'login': 'alumno_count_1@test.local',
        })
        user2 = self.env['res.users'].create({
            'name': 'Alumno Count Test 2',
            'login': 'alumno_count_2@test.local',
        })
        actividad.write({'alumno_ids': [(4, user1.id), (4, user2.id)]})
        self.assertEqual(actividad.alumno_count, 2)

    def test_estado_code_related(self):
        """estado_code debe reflejar el code del estado asignado."""
        actividad = self._make_actividad(estado_id=self.estado_aprobada.id)
        self.assertEqual(actividad.estado_code, 'aprobada')

    # ── Cron: actualizar estados por fecha ───────────────────────────────────

    def test_cron_pendiente_a_en_curso(self):
        """El cron debe pasar actividades de pendiente_inicio a en_curso al llegar fecha_inicio."""
        ayer = date.today() - timedelta(days=1)
        manana = date.today() + timedelta(days=1)
        actividad = self.env['actividad.complementaria'].with_context(
            skip_fecha_check=True
        ).create({
            'name': 'Actividad cron pendiente',
            'tipo_actividad_id': self.tipo.id,
            'periodo': self.periodo.id,
            'fecha_inicio': ayer,
            'fecha_fin': manana,
            'cantidad_horas': 4.0,
            'estado_id': self.estado_pendiente.id,
        })
        self.env['actividad.complementaria']._actualizar_estado_por_fecha()
        self.assertEqual(actividad.estado_code, 'en_curso')

    def test_cron_en_curso_a_finalizada(self):
        """El cron debe pasar actividades de en_curso a finalizada al llegar fecha_fin."""
        hace_dos_dias = date.today() - timedelta(days=2)
        ayer = date.today() - timedelta(days=1)
        actividad = self.env['actividad.complementaria'].with_context(
            skip_fecha_check=True
        ).create({
            'name': 'Actividad cron en curso',
            'tipo_actividad_id': self.tipo.id,
            'periodo': self.periodo.id,
            'fecha_inicio': hace_dos_dias,
            'fecha_fin': ayer,
            'cantidad_horas': 4.0,
            'estado_id': self.estado_en_curso.id,
        })
        self.env['actividad.complementaria']._actualizar_estado_por_fecha()
        self.assertEqual(actividad.estado_code, 'finalizada')
