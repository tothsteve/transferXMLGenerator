from django import forms
from .models import Transfer, Beneficiary, BankAccount, TransferTemplate

class TransferForm(forms.ModelForm):
    class Meta:
        model = Transfer
        fields = ['originator_account', 'beneficiary', 'amount', 'currency', 'execution_date', 'remittance_info']
        widgets = {
            'execution_date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'remittance_info': forms.TextInput(attrs={'placeholder': 'Közlemény szövege'}),
        }

class BeneficiaryForm(forms.ModelForm):
    class Meta:
        model = Beneficiary
        fields = ['name', 'account_number', 'description', 'is_frequent']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Kedvezményezett neve'}),
            'account_number': forms.TextInput(attrs={'placeholder': 'XXXXXXXX-XXXXXXXX-XXXXXXXX'}),
            'description': forms.TextInput(attrs={'placeholder': 'Leírás (opcionális)'}),
        }

class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ['name', 'account_number', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Számla neve'}),
            'account_number': forms.TextInput(attrs={'placeholder': 'XXXXXXXX-XXXXXXXX-XXXXXXXX'}),
        }

class UploadExcelForm(forms.Form):
    excel_file = forms.FileField(
        label='Excel fájl',
        help_text='Válassza ki az Excel fájlt (.xlsx)',
        widget=forms.FileInput(attrs={'accept': '.xlsx,.xls'})
    )
    account_number = forms.CharField(
        label='Terhelendő számlaszám',
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'XXXXXXXX-XXXXXXXX-XXXXXXXX'})
    )
