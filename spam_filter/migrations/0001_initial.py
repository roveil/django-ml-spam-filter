# Generated by Django 2.2.4 on 2019-09-23 10:41

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BayesDictionary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(db_index=True, max_length=255, unique=True)),
                ('spam_count', models.PositiveIntegerField(default=0)),
                ('ham_count', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='LearningMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('spam', models.BooleanField()),
                ('processed', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='NNStructure',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weights', models.BinaryField()),
            ],
        ),
        migrations.RunSQL("CREATE UNIQUE INDEX IF NOT EXISTS unique_nnstructure_index "
                          "ON spam_filter_nnstructure ((id IS NOT NULL));",
                          reverse_sql="DROP INDEX IF EXISTS unique_nnstructure_index;",
                          hints={'model_name': 'spam_filter.NNStructure'})
    ]
