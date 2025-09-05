from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatthread',
            name='archived',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]

