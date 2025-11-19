from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0003_add_citations'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='inline_refs',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
