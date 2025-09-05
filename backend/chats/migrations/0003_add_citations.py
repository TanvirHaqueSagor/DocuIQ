from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0002_add_archived'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='citations',
            field=models.JSONField(blank=True, default=list),
        ),
    ]

