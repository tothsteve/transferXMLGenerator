# Generated manually for renaming Beneficiary fields
# This migration renames bank_name to description and notes to remittance_information

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank_transfers', '0002_templatebeneficiary_alter_bankaccount_options_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='beneficiary',
            old_name='bank_name',
            new_name='description',
        ),
        migrations.RenameField(
            model_name='beneficiary',
            old_name='notes',
            new_name='remittance_information',
        ),
        migrations.AlterField(
            model_name='beneficiary',
            name='description',
            field=models.CharField(blank=True, help_text='További információk a kedvezményezettről (bank neve, szervezet adatai, stb.)', max_length=200, verbose_name='Leírás'),
        ),
        migrations.AlterField(
            model_name='beneficiary',
            name='remittance_information',
            field=models.TextField(blank=True, help_text='Alapértelmezett fizetési hivatkozások, számlaszámok vagy egyéb tranzakció-specifikus információk', verbose_name='Utalási információ'),
        ),
    ]