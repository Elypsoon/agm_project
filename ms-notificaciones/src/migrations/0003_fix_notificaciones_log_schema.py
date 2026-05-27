"""
Migration 0003: Fix notificaciones_log table schema mismatch.

The table was created with an old schema (bigint id, varchar destinatario_id, 
varchar tipo/estado with different max_lengths). The model now uses UUIDField
for the primary key. This migration drops and recreates the table to match the 
current model definition exactly.
"""

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0002_alter_notificationlog_tipo'),
    ]

    operations = [
        # Drop old table and recreate with the correct UUID-based schema
        migrations.RunSQL(
            sql="""
                DROP TABLE IF EXISTS notificaciones_log CASCADE;

                CREATE TABLE notificaciones_log (
                    id                 UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
                    tipo               VARCHAR(50)   NOT NULL,
                    destinatario_email VARCHAR(255)  NOT NULL,
                    destinatario_id    UUID,
                    asunto             VARCHAR(255)  NOT NULL,
                    contenido          TEXT          NOT NULL,
                    estado             VARCHAR(20)   NOT NULL DEFAULT 'pendiente',
                    error_detalle      TEXT,
                    metadata           JSONB         NOT NULL DEFAULT '{}',
                    created_at         TIMESTAMPTZ   NOT NULL DEFAULT NOW()
                );
            """,
            reverse_sql="""
                DROP TABLE IF EXISTS notificaciones_log CASCADE;
            """,
        ),
    ]
