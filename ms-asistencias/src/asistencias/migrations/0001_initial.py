import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Sesion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('materia_id', models.UUIDField()),
                ('docente_id', models.UUIDField()),
                ('fecha', models.DateField(auto_now_add=True)),
                ('hora_inicio', models.DateTimeField(auto_now_add=True)),
                ('hora_fin', models.DateTimeField(blank=True, null=True)),
                ('estado', models.CharField(choices=[('activa', 'Activa'), ('cerrada', 'Cerrada')], default='activa', max_length=10)),
                ('duracion_segundos', models.IntegerField(default=600)),
            ],
            options={
                'db_table': 'sesiones',
                'ordering': ['-hora_inicio'],
            },
        ),
        migrations.CreateModel(
            name='Asistencia',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('alumno_id', models.UUIDField()),
                ('materia_id', models.UUIDField()),
                ('matricula', models.CharField(max_length=20)),
                ('estado', models.CharField(choices=[('presente', 'Presente'), ('retardo', 'Retardo'), ('ausente', 'Ausente')], default='presente', max_length=10)),
                ('hora_registro', models.DateTimeField(auto_now_add=True)),
                ('qr_token_hash', models.CharField(max_length=64, unique=True)),
                ('sesion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asistencias', to='asistencias.sesion')),
            ],
            options={
                'db_table': 'asistencias',
                'ordering': ['-hora_registro'],
                'unique_together': {('sesion', 'alumno_id')},
            },
        ),
    ]