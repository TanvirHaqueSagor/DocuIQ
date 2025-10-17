from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_userprofile_role_alter_userprofile_id_organization_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='plan',
            field=models.CharField(choices=[('starter', 'Starter'), ('pro', 'Pro'), ('enterprise', 'Enterprise')], default='starter', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='plan',
            field=models.CharField(choices=[('starter', 'Starter'), ('pro', 'Pro'), ('enterprise', 'Enterprise')], default='starter', max_length=20),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='SalesInquiry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254)),
                ('company', models.CharField(blank=True, max_length=200)),
                ('role', models.CharField(blank=True, max_length=120)),
                ('desired_plan', models.CharField(choices=[('starter', 'Starter'), ('pro', 'Pro'), ('enterprise', 'Enterprise')], default='enterprise', max_length=20)),
                ('message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
    ]
