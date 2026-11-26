from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('diary', '0002_habit')]
    # The implicit M2M table already has these columns and the unique index.
    operations = [migrations.SeparateDatabaseAndState(state_operations=[
        migrations.CreateModel(name='HabitMark', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('habit', models.ForeignKey(on_delete=models.CASCADE, to='diary.habit')),
            ('entry', models.ForeignKey(db_column='dailyentry_id', on_delete=models.CASCADE, to='diary.dailyentry')),
        ], options={'db_table': 'diary_habit_completed_days', 'unique_together': {('habit', 'entry')}}),
        migrations.AlterField(model_name='habit', name='completed_days', field=models.ManyToManyField(
            blank=True, related_name='completed_habits', through='diary.HabitMark', to='diary.dailyentry')),
    ])]
