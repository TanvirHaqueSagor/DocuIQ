from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0002_alter_ingestfile_file_alter_ingestjob_mode_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingestjob',
            name='state',
            field=models.CharField(db_index=True, default='QUEUED', max_length=24),
        ),
        migrations.AddField(
            model_name='ingestjob',
            name='error_text',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ingestjob',
            name='totals_json',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='ingestfile',
            name='status',
            field=models.CharField(db_index=True, default='QUEUED', max_length=24),
        ),
        migrations.AddField(
            model_name='ingestfile',
            name='status_updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='ingestfile',
            name='error_code',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='ingestfile',
            name='error_text',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ingestfile',
            name='steps_json',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='ingestfile',
            name='indexed_bool',
            field=models.BooleanField(default=False),
        ),
    ]

