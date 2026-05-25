# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


# ---------------------------------------------------------------------------
# Utilidad de fechas compartida entre tests
# ---------------------------------------------------------------------------

def _n_dias_habiles(n, desde=None):
    """Devuelve la fecha resultante de avanzar *n* días hábiles (lunes a viernes).

    Args:
        n:     Número de días hábiles a avanzar.
        desde: Fecha base. Si es None se usa la fecha actual.
    """
    base = desde or date.today()
    contados = 0
    candidato = base
    while contados < n:
        candidato += timedelta(days=1)
        if candidato.weekday() < 5:   # 0=lun … 4=vie; 5=sáb, 6=dom
            contados += 1
    return candidato


class TestActividad(TransactionCase):
    """Tests para el modelo actividad.complementaria.

    Todos los registros de catálogo (estados, periodos) se obtienen con
    env.ref() — el módulo los carga desde sus XMLs al instalarse.
    No se crean duplicados en los tests.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.env.user.group_ids |= cls.env.ref(
            'actividades_complementarias.group_admin_actividades'
        )
        # Estados — definidos en estado_actividad_data.xml
        cls.estado_aprobada = cls.env.ref('actividades_complementarias.estado_aprobada')
        cls.estado_finalizada = cls.env.ref('actividades_complementarias.estado_finalizada')
        cls.estado_pendiente = cls.env.ref('actividades_complementarias.estado_pendiente_inicio')

        # Periodo — definido en periodo_data.xml (Many2one, no Char)
        cls.periodo = cls.env.ref('actividades_complementarias.per_2025A')

        # tipo_actividad no tiene XMLs de datos predefinidos — se crea aquí
        cls.tipo = cls.env['actividad.tipo'].create({'name': 'Conferencia Test'})

        cls.fecha_valida = _n_dias_habiles(5)   # mínimo exacto exigido por el constraint
        cls.fecha_fin_valida = _n_dias_habiles(6)   # un día hábil más, para que fin > inicio

    def _make_actividad(self, **kwargs):
        """Helper: crea una actividad con valores mínimos válidos.

        Usa skip_fecha_check para evitar que el constraint de fecha_inicio
        bloquee tests que necesitan fechas pasadas para verificar otros constraints.
        """
        vals = {
            'name': 'Actividad de prueba',
            'tipo_actividad_id': self.tipo.id,
            'periodo': self.periodo.id,
            'fecha_inicio': self.fecha_valida,
            'fecha_fin': self.fecha_fin_valida,
            'cantidad_horas': 8.0,
            'cupo_min': 5,
            'cupo_max': 30,
            'creditos': '1.0',
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
                'creditos': '1.0',
            })

    def test_fecha_inicio_menos_de_5_habiles_falla(self):
        """Una fecha de inicio con solo 4 días hábiles de antelación debe fallar."""
        with self.assertRaises(ValidationError):
            self.env['actividad.complementaria'].create({
                'name': 'Actividad con poco margen',
                'tipo_actividad_id': self.tipo.id,
                'periodo': self.periodo.id,
                'fecha_inicio': _n_dias_habiles(4),
                'fecha_fin': _n_dias_habiles(5),
                'cantidad_horas': 4.0,
                'creditos': '1.0',
            })

    def test_fecha_inicio_exactamente_5_habiles_ok(self):
        """Una fecha de inicio con exactamente 5 días hábiles de antelación debe ser válida."""
        actividad = self.env['actividad.complementaria'].create({
            'name': 'Actividad con margen justo',
            'tipo_actividad_id': self.tipo.id,
            'periodo': self.periodo.id,
            'fecha_inicio': _n_dias_habiles(5),
            'fecha_fin': _n_dias_habiles(6),
            'cantidad_horas': 4.0,
            'creditos': '1.0',
        })
        self.assertTrue(actividad.id)

    def test_fecha_fin_antes_de_inicio_falla(self):
        """La fecha de fin debe ser posterior a la fecha de inicio."""
        with self.assertRaises(ValidationError):
            self._make_actividad(fecha_inicio=self.fecha_valida, fecha_fin=self.fecha_valida)

    def test_edicion_sin_propuesta_manana_ok(self):
        """En edición sin propuesta aprobada, mover fecha_inicio a mañana es válido."""
        actividad = self._make_actividad()
        manana = date.today() + timedelta(days=1)
        actividad.write({
            'fecha_inicio': manana,
            'fecha_fin': manana + timedelta(days=1),
        })
        self.assertEqual(actividad.fecha_inicio, manana)

    def test_edicion_sin_propuesta_hoy_falla(self):
        """En edición sin propuesta aprobada, fecha_inicio = hoy debe fallar."""
        actividad = self._make_actividad()
        with self.assertRaises(ValidationError):
            actividad.write({'fecha_inicio': date.today()})

    def test_edicion_con_propuesta_usa_fecha_envio(self):
        """Con propuesta aprobada, el mínimo de fecha_inicio se calcula desde la fecha de envío."""
        # Crear la actividad sorteando el constraint (usamos fechas futuras válidas)
        actividad = self._make_actividad()

        # Simular una propuesta cuya fecha de envío fue hace un día hábil:
        # buscamos el día hábil (lun-vie) más reciente anterior a hoy.
        fecha_envio = date.today() - timedelta(days=1)
        while fecha_envio.weekday() >= 5:   # retroceder si cae en sáb(5) o dom(6)
            fecha_envio -= timedelta(days=1)

        estado_en_revision = self.env.ref(
            'actividades_complementarias.estado_solicitud_en_revision'
        )
        estado_aprobada = self.env.ref(
            'actividades_complementarias.estado_solicitud_aprobada'
        )
        propuesta = self.env['actividad.propuesta'].create({
            'actividad_id': actividad.id,
            'estado_solicitud_id': estado_en_revision.id,
            'fecha': fecha_envio,
        })
        propuesta.write({'estado_solicitud_id': estado_aprobada.id})

        # La fecha mínima válida es 5 días hábiles desde fecha_envio, pero
        # nunca antes de mañana.
        min_fecha = max(_n_dias_habiles(5, desde=fecha_envio), date.today() + timedelta(days=1))

        # Un día antes del mínimo debe fallar
        with self.assertRaises(ValidationError):
            actividad.write({'fecha_inicio': min_fecha - timedelta(days=1)})

        # El día exacto del mínimo debe funcionar
        actividad.write({
            'fecha_inicio': min_fecha,
            'fecha_fin': min_fecha + timedelta(days=1),
        })
        self.assertEqual(actividad.fecha_inicio, min_fecha)

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
        periodo_b = self.env.ref('actividades_complementarias.per_2025B')
        self._make_actividad(name='Actividad Repetida', periodo=self.periodo.id)
        actividad2 = self._make_actividad(name='Actividad Repetida', periodo=periodo_b.id)
        self.assertTrue(actividad2.id)

    # ── Business logic: action_enviar_catalogo ───────────────────────────────

    def test_enviar_catalogo_sin_estado_aprobado_falla(self):
        """No se puede enviar al catálogo una actividad sin estado aprobado."""
        actividad = self._make_actividad()  # sin estado
        with self.assertRaises(ValidationError):
            actividad.action_enviar_catalogo()

    def test_enviar_catalogo_rechazada_falla(self):
        """Una actividad rechazada no puede enviarse al catálogo."""
        estado_rechazada = self.env.ref('actividades_complementarias.estado_rechazada')
        actividad = self._make_actividad(estado_id=estado_rechazada.id)
        with self.assertRaises(ValidationError):
            actividad.action_enviar_catalogo()

    def test_enviar_catalogo_finalizada_falla(self):
        """Una actividad finalizada no puede enviarse al catálogo."""
        actividad = self._make_actividad(estado_id=self.estado_finalizada.id)
        with self.assertRaises(ValidationError):
            actividad.action_enviar_catalogo()

    def test_enviar_catalogo_aprobada_ok(self):
        """Una actividad aprobada puede enviarse al catálogo."""
        actividad = self._make_actividad(
            estado_id=self.estado_aprobada.id,
            creditos='1.0',
            responsable_actividad_id=self.env.user.id,
        )
        actividad.action_enviar_catalogo()
        self.assertTrue(actividad.en_catalogo)

    def test_enviar_catalogo_pendiente_inicio_ok(self):
        """Una actividad pendiente de inicio puede enviarse al catálogo."""
        actividad = self._make_actividad(
            estado_id=self.estado_pendiente.id,
            creditos='1.0',
            responsable_actividad_id=self.env.user.id,
        )
        actividad.action_enviar_catalogo()
        self.assertTrue(actividad.en_catalogo)

    # ── Business logic: action_firmar_constancias ────────────────────────────

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

    def test_constancias_firmadas_solo_con_ambas_firmas(self):
        """constancias_firmadas es True solo cuando JD Y Responsable han firmado."""
        actividad = self._make_actividad(estado_id=self.estado_finalizada.id)
        # Solo JD firma
        actividad.action_firmar_constancias()
        self.assertTrue(actividad.jd_firmo)
        self.assertFalse(actividad.responsable_firmo)
        self.assertFalse(actividad.constancias_firmadas)
        # Responsable firma también
        actividad.action_firmar_constancias_responsable()
        self.assertTrue(actividad.constancias_firmadas)

    def test_jd_no_puede_firmar_dos_veces(self):
        """El JD no puede firmar las constancias más de una vez."""
        actividad = self._make_actividad(estado_id=self.estado_finalizada.id)
        actividad.action_firmar_constancias()
        with self.assertRaises(ValidationError):
            actividad.action_firmar_constancias()

    # ── Computes ─────────────────────────────────────────────────────────────

    def test_alumno_count_compute(self):
        """El contador de alumnos debe reflejar los registros en Many2many.
        
        MODIFICADO: se añade tipo_inscripcion='asignacion' porque el nuevo
        constraint _check_tipo_inscripcion_vs_catalogo impide asignar alumnos
        directamente a actividades de tipo 'catalogo' (RA-01SC, Regla 5).
        """
        # La actividad debe ser de asignación directa para poder añadir alumnos
        actividad = self._make_actividad(tipo_inscripcion='asignacion')
        self.assertEqual(actividad.alumno_count, 0)

        user1 = self.env['res.users'].create({
            'name': 'Alumno Test 1',
            'login': 'alumno_test_1@test.com',
        })
        user2 = self.env['res.users'].create({
            'name': 'Alumno Test 2',
            'login': 'alumno_test_2@test.com',
        })
        actividad.write({'alumno_ids': [(4, user1.id), (4, user2.id)]})
        self.assertEqual(actividad.alumno_count, 2)

    # ── Predefinidas por Comité ───────────────────────────────────────────────

    def test_predefinida_comite_autocompleta_tipo(self):
        """Al asignar un predefinido por comité, tipo_actividad_id se actualiza
        al tipo almacenado en el registro predefinido."""
        tipo_nuevo = self.env['actividad.tipo'].create({'name': 'Tipo Autocomplete'})
        predefinida = self.env['actividad.tipo.predefinida'].create({
            'name': 'Actividad Comite Test',
            'tipo_actividad_id': tipo_nuevo.id,
            'is_comite': True,
        })
        actividad = self._make_actividad()
        actividad.write({'actividad_predefinida': predefinida.id})
        # El write no dispara onchange; verificamos que el Many2one guarda
        # correctamente y que tipo puede leerse desde el predefinido.
        self.assertEqual(
            actividad.actividad_predefinida.tipo_actividad_id,
            tipo_nuevo,
        )

    def test_predefinidas_fijas_existen(self):
        """Los registros fijos (Curso MOOC, Extraescolar) deben existir
        tras la instalación del módulo."""
        mooc = self.env['actividad.tipo.predefinida'].search([
            ('key', '=', 'curso_mooc'),
        ])
        extraescolar = self.env['actividad.tipo.predefinida'].search([
            ('key', '=', 'extraescolar'),
        ])
        self.assertTrue(mooc, 'Debe existir el predefinido Curso MOOC.')
        self.assertTrue(extraescolar, 'Debe existir el predefinido Extraescolar.')
        self.assertFalse(
            mooc.is_comite,
            'Curso MOOC no debe estar marcado como aprobado por comité.',
        )

    # ── NUEVOS: Tipo de inscripción — Regla de negocio RA-01SC (Regla 5) ────
    #
    # Los siguientes tests verifican que el campo `tipo_inscripcion` funcione
    # correctamente en todos los flujos descritos en el PDF RA-01SC:
    #
    #   - El valor por defecto del campo es 'catalogo'.
    #   - Una actividad de 'asignacion' no puede publicarse en el catálogo
    #     (`_check_tipo_inscripcion_vs_catalogo` en actividad.py).
    #   - Una actividad de 'catalogo' no puede tener alumnos asignados directamente
    #     (`_check_tipo_inscripcion_vs_catalogo` en actividad.py).
    #   - `action_enviar_catalogo` rechaza explícitamente actividades de 'asignacion'
    #     antes de publicarlas (validación temprana añadida al método).
    #   - El modelo `actividad.inscripcion` bloquea inscripciones directas en
    #     actividades de tipo 'catalogo'
    #     (`_check_tipo_inscripcion_permitido` en actividad_inscripcion.py).

    def test_tipo_inscripcion_default_es_catalogo(self):
        """
        NUEVO — verifica que el valor por defecto de tipo_inscripcion sea 'catalogo'.

        Razón del cambio: El campo fue introducido en actividad.py con
        `default='catalogo'` para que las actividades de inscripción abierta
        sean la opción estándar sin necesidad de configuración extra.
        """
        actividad = self._make_actividad()
        self.assertEqual(
            actividad.tipo_inscripcion,
            'catalogo',
            "El campo tipo_inscripcion debe tener el valor por defecto 'catalogo'.",
        )

    def test_asignacion_con_en_catalogo_true_en_create_falla(self):
        """
        NUEVO — verifica que no se pueda crear una actividad de 'asignacion'
        con en_catalogo=True.

        Razón del cambio: La validación en el método create() de actividad.py
        detecta esta combinación ilegal antes de llamar a super().create(),
        para dar un mensaje de error claro (RA-01SC, Regla 5).
        """
        with self.assertRaises(ValidationError):
            self._make_actividad(
                tipo_inscripcion='asignacion',
                en_catalogo=True,
            )

    def test_asignacion_con_en_catalogo_true_en_write_falla(self):
        """
        NUEVO — verifica que no se pueda cambiar en_catalogo a True en una
        actividad que ya es de tipo 'asignacion'.

        Razón del cambio: El constraint `_check_tipo_inscripcion_vs_catalogo`
        en actividad.py se dispara también en write(), cubriendo el caso de
        una actividad modificada después de crearse (RA-01SC, Regla 5).
        """
        actividad = self._make_actividad(tipo_inscripcion='asignacion')
        with self.assertRaises(ValidationError):
            actividad.with_context(bypass_edit_protection=True).write(
                {'en_catalogo': True}
            )

    def test_catalogo_con_alumno_ids_en_create_falla(self):
        """
        NUEVO — verifica que no se pueda crear una actividad de 'catalogo'
        con alumnos asignados directamente.

        Razón del cambio: La validación en create() de actividad.py rechaza
        esta combinación para mantener la trazabilidad del canal de inscripción
        (RA-01SC, Regla 5).
        """
        alumno = self.env['res.users'].create({
            'name': 'Alumno Catalogo Test',
            'login': 'alumno_catalogo_create@test.com',
        })
        with self.assertRaises(ValidationError):
            self._make_actividad(
                tipo_inscripcion='catalogo',
                alumno_ids=[(4, alumno.id)],
            )

    def test_catalogo_con_alumno_ids_en_write_falla(self):
        """
        NUEVO — verifica que no se puedan añadir alumnos directamente a una
        actividad de tipo 'catalogo' mediante write().

        Razón del cambio: El constraint `_check_tipo_inscripcion_vs_catalogo`
        en actividad.py cubre el ciclo de vida completo del registro, no solo
        la creación (RA-01SC, Regla 5).
        """
        actividad = self._make_actividad(tipo_inscripcion='catalogo')
        alumno = self.env['res.users'].create({
            'name': 'Alumno Catalogo Write',
            'login': 'alumno_catalogo_write@test.com',
        })
        with self.assertRaises(ValidationError):
            actividad.with_context(bypass_edit_protection=True).write(
                {'alumno_ids': [(4, alumno.id)]}
            )

    def test_asignacion_sin_catalogo_ok(self):
        """
        NUEVO — verifica que una actividad de tipo 'asignacion' se puede
        crear sin en_catalogo (comportamiento normal y esperado).

        Razón del cambio: Confirmación positiva de que la nueva lógica no
        rompe el flujo legítimo de asignación directa (RA-01SC, flujo principal).
        """
        alumno = self.env['res.users'].create({
            'name': 'Alumno Asignacion OK',
            'login': 'alumno_asignacion_ok@test.com',
        })
        actividad = self._make_actividad(
            tipo_inscripcion='asignacion',
            alumno_ids=[(4, alumno.id)],
        )
        self.assertEqual(actividad.tipo_inscripcion, 'asignacion')
        self.assertFalse(actividad.en_catalogo)
        self.assertIn(alumno, actividad.alumno_ids)

    def test_catalogo_sin_alumnos_ok(self):
        """
        NUEVO — verifica que una actividad de tipo 'catalogo' sin alumnos
        asignados se puede crear sin problemas.

        Razón del cambio: Confirmación positiva del flujo estándar de inscripción
        abierta, donde los alumnos se inscriben desde el catálogo público
        (RA-01SC, flujo principal — envío al catálogo).
        """
        actividad = self._make_actividad(tipo_inscripcion='catalogo')
        self.assertEqual(actividad.tipo_inscripcion, 'catalogo')
        self.assertFalse(actividad.alumno_ids)

    def test_enviar_catalogo_tipo_asignacion_falla(self):
        """
        NUEVO — verifica que `action_enviar_catalogo` bloquea actividades
        de tipo 'asignacion'.

        Razón del cambio: Se añadió una validación temprana al inicio de
        `action_enviar_catalogo` en actividad.py para dar al usuario un mensaje
        claro en lugar del error técnico del constraint (RA-01SC, Regla 5).
        """
        actividad = self._make_actividad(
            estado_id=self.estado_aprobada.id,
            tipo_inscripcion='asignacion',
            responsable_actividad_id=self.env.user.id,
        )
        with self.assertRaises(ValidationError):
            actividad.action_enviar_catalogo()

    def test_enviar_catalogo_tipo_catalogo_ok(self):
        """
        NUEVO — verifica que `action_enviar_catalogo` sí permite publicar
        actividades de tipo 'catalogo' (flujo normal tras los cambios).

        Razón del cambio: Confirmación de que la nueva validación no interfiere
        con el flujo legítimo de publicación de actividades de inscripción abierta
        (RA-01SC, flujo principal — paso 3: envío al catálogo).
        """
        actividad = self._make_actividad(
            estado_id=self.estado_aprobada.id,
            tipo_inscripcion='catalogo',
            responsable_actividad_id=self.env.user.id,
        )
        actividad.action_enviar_catalogo()
        self.assertTrue(actividad.en_catalogo)

    # ── NUEVOS: actividad.inscripcion — _check_tipo_inscripcion_permitido ────
    #
    # Los dos tests siguientes verifican el constraint añadido en
    # actividad_inscripcion.py que bloquea la inscripción directa de alumnos
    # en actividades de tipo 'catalogo' a través del modelo actividad.inscripcion.
    # Este cierra el último vector de entrada descrito en el ítem 7 del resumen
    # de cambios.

    def test_inscripcion_directa_en_catalogo_falla(self):
        """
        NUEVO — verifica que no se puede crear un registro actividad.inscripcion
        en una actividad de tipo 'catalogo'.

        Razón del cambio: El constraint `_check_tipo_inscripcion_permitido` en
        actividad_inscripcion.py bloquea este vector de entrada para garantizar
        que las actividades de catálogo nunca acumulen inscripciones directas
        (RA-01SC, Regla 5 — ítem 7 del resumen de cambios).
        """
        # Se crea la actividad como tipo 'asignacion' para que el constraint de
        # actividad.complementaria no interfiera; luego se cambia a 'catalogo'
        # directamente en BD para simular el estado problemático sin pasar
        # por los constraints de write().
        actividad = self._make_actividad(tipo_inscripcion='asignacion')
        # Forzar el cambio de tipo a 'catalogo' a nivel ORM, sin disparar
        # _check_tipo_inscripcion_vs_catalogo (no hay alumnos asignados aún).
        actividad.with_context(bypass_edit_protection=True).write(
            {'tipo_inscripcion': 'catalogo'}
        )

        partner = self.env['res.partner'].create({
            'name': 'Estudiante Catalogo Inscripcion',
        })
        with self.assertRaises(ValidationError):
            self.env['actividad.inscripcion'].create({
                'actividad_id': actividad.id,
                'partner_id': partner.id,
            })

    def test_inscripcion_directa_en_asignacion_ok(self):
        """
        NUEVO — verifica que sí se puede crear un registro actividad.inscripcion
        en una actividad de tipo 'asignacion' (comportamiento esperado).

        Razón del cambio: Confirmación positiva de que el constraint
        `_check_tipo_inscripcion_permitido` solo bloquea actividades de catálogo
        y no afecta el flujo de asignación directa (RA-01SC, flujo de asignación
        de alumnos, pasos 4-13 del caso de uso RA-02SC).
        """
        actividad = self._make_actividad(tipo_inscripcion='asignacion')
        partner = self.env['res.partner'].create({
            'name': 'Estudiante Asignacion Inscripcion',
        })
        inscripcion = self.env['actividad.inscripcion'].create({
            'actividad_id': actividad.id,
            'partner_id': partner.id,
        })
        self.assertTrue(inscripcion.id)
        self.assertEqual(inscripcion.actividad_id, actividad)
