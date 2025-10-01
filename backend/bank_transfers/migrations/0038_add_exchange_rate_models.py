# Generated manually for MNB exchange rate integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank_transfers', '0037_beneficiary_tax_number_alter_beneficiary_vat_number_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExchangeRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('rate_date', models.DateField(db_index=True, verbose_name='Árfolyam dátuma')),
                ('currency', models.CharField(choices=[('USD', 'US Dollar'), ('EUR', 'Euro')], help_text='Currency code (USD or EUR)', max_length=3, verbose_name='Deviza kód')),
                ('rate', models.DecimalField(decimal_places=6, help_text='Exchange rate: 1 unit of currency = X HUF', max_digits=12, verbose_name='Árfolyam (HUF)')),
                ('unit', models.IntegerField(default=1, help_text='Number of currency units this rate applies to (typically 1)', verbose_name='Egység')),
                ('sync_date', models.DateTimeField(auto_now_add=True, help_text='When this rate was fetched from MNB', verbose_name='Szinkronizálva')),
                ('source', models.CharField(default='MNB', help_text='Data source (always MNB for official rates)', max_length=20, verbose_name='Forrás')),
            ],
            options={
                'verbose_name': 'Árfolyam',
                'verbose_name_plural': 'Árfolyamok',
                'ordering': ['-rate_date', 'currency'],
                'unique_together': {('rate_date', 'currency')},
            },
        ),
        migrations.CreateModel(
            name='ExchangeRateSyncLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sync_start_time', models.DateTimeField(verbose_name='Szinkronizáció kezdete')),
                ('sync_end_time', models.DateTimeField(blank=True, null=True, verbose_name='Szinkronizáció vége')),
                ('currencies_synced', models.CharField(help_text="Comma-separated currency codes (e.g., 'USD,EUR')", max_length=50, verbose_name='Szinkronizált devizák')),
                ('date_range_start', models.DateField(verbose_name='Dátum tartomány kezdete')),
                ('date_range_end', models.DateField(verbose_name='Dátum tartomány vége')),
                ('rates_created', models.IntegerField(default=0, help_text='Number of new exchange rates created', verbose_name='Létrehozott árfolyamok')),
                ('rates_updated', models.IntegerField(default=0, help_text='Number of existing exchange rates updated', verbose_name='Frissített árfolyamok')),
                ('sync_status', models.CharField(choices=[('RUNNING', 'Futás'), ('SUCCESS', 'Sikeres'), ('PARTIAL_SUCCESS', 'Részlegesen sikeres'), ('FAILED', 'Sikertelen')], default='RUNNING', max_length=20, verbose_name='Szinkronizáció státusza')),
                ('error_message', models.TextField(blank=True, help_text='Error details if sync failed', verbose_name='Hibaüzenet')),
            ],
            options={
                'verbose_name': 'Árfolyam szinkronizáció napló',
                'verbose_name_plural': 'Árfolyam szinkronizáció naplók',
                'ordering': ['-sync_start_time'],
            },
        ),
        migrations.AddIndex(
            model_name='exchangerate',
            index=models.Index(fields=['rate_date', 'currency'], name='bank_transf_rate_da_7f3e8a_idx'),
        ),
        migrations.AddIndex(
            model_name='exchangerate',
            index=models.Index(fields=['-rate_date'], name='bank_transf_rate_da_e1b2f5_idx'),
        ),
        migrations.AddIndex(
            model_name='exchangerate',
            index=models.Index(fields=['currency'], name='bank_transf_currenc_a5c7d2_idx'),
        ),
        migrations.AddIndex(
            model_name='exchangeratesynclog',
            index=models.Index(fields=['-sync_start_time'], name='bank_transf_sync_st_4b9c6d_idx'),
        ),
        migrations.AddIndex(
            model_name='exchangeratesynclog',
            index=models.Index(fields=['sync_status'], name='bank_transf_sync_st_2e8a1f_idx'),
        ),
    ]
