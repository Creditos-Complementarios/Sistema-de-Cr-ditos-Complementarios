# -*- coding: utf-8 -*-
"""
Migración 19.0.1.0.0 → 19.0.1.1.0
====================================
- Renombra certificate_signed → jd_signed en actividad_inscripcion
- Agrega columna ra_signed en actividad_inscripcion
"""


def migrate(cr, version):
    if not version:
        return

    # Renombrar certificate_signed a jd_signed
    cr.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'actividad_inscripcion'
                  AND column_name = 'certificate_signed'
            ) THEN
                ALTER TABLE actividad_inscripcion
                    RENAME COLUMN certificate_signed TO jd_signed;
            END IF;
        END$$;
    """)

    # Agregar ra_signed si no existe
    cr.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'actividad_inscripcion'
                  AND column_name = 'ra_signed'
            ) THEN
                ALTER TABLE actividad_inscripcion
                    ADD COLUMN ra_signed BOOLEAN NOT NULL DEFAULT FALSE;
            END IF;
        END$$;
    """)
