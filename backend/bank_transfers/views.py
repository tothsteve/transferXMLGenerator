from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from .models import BankAccount, Beneficiary, Transfer, TransferTemplate, TransferBatch
from .forms import TransferForm, BeneficiaryForm, BankAccountForm, UploadExcelForm
from .utils import generate_xml, parse_excel_file
import json
from datetime import date

def index(request):
    """Főoldal - utalások létrehozása"""
    default_account = BankAccount.objects.filter(is_default=True).first()
    frequent_beneficiaries = Beneficiary.objects.filter(is_frequent=True)
    
    context = {
        'default_account': default_account,
        'frequent_beneficiaries': frequent_beneficiaries,
        'today': date.today(),
    }
    return render(request, 'bank_transfers/index.html', context)

def create_transfer(request):
    """Új utalás létrehozása"""
    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            transfer = form.save()
            messages.success(request, f'Utalás sikeresen létrehozva: {transfer.beneficiary.name}')
            return redirect('index')
    else:
        form = TransferForm()
    
    return render(request, 'bank_transfers/create_transfer.html', {'form': form})

def beneficiaries(request):
    """Kedvezményezettek kezelése"""
    beneficiaries = Beneficiary.objects.all().order_by('name')
    form = BeneficiaryForm()
    
    if request.method == 'POST':
        form = BeneficiaryForm(request.POST)
        if form.is_valid():
            beneficiary = form.save()
            messages.success(request, f'Kedvezményezett sikeresen létrehozva: {beneficiary.name}')
            return redirect('beneficiaries')
    
    context = {
        'beneficiaries': beneficiaries,
        'form': form,
    }
    return render(request, 'bank_transfers/beneficiaries.html', context)

def accounts(request):
    """Bank számlák kezelése"""
    accounts = BankAccount.objects.all().order_by('name')
    form = BankAccountForm()
    
    if request.method == 'POST':
        form = BankAccountForm(request.POST)
        if form.is_valid():
            account = form.save()
            messages.success(request, f'Bank számla sikeresen létrehozva: {account.name}')
            return redirect('accounts')
    
    context = {
        'accounts': accounts,
        'form': form,
    }
    return render(request, 'bank_transfers/accounts.html', context)

def generate_xml_view(request):
    """XML generálás"""
    if request.method == 'POST':
        data = json.loads(request.body)
        transfer_ids = data.get('transfer_ids', [])
        
        if not transfer_ids:
            return JsonResponse({'error': 'Nincs kiválasztott utalás'}, status=400)
        
        transfers = Transfer.objects.filter(id__in=transfer_ids)
        xml_content = generate_xml(transfers)
        
        # Opcionálisan mentés kötegbe
        batch_name = data.get('batch_name')
        if batch_name:
            batch = TransferBatch.objects.create(
                name=batch_name,
                xml_generated_at=timezone.now()
            )
            batch.transfers.set(transfers)
        
        return JsonResponse({
            'xml': xml_content,
            'count': len(transfers)
        })
    
    # GET request - show transfers to select
    transfers = Transfer.objects.select_related('originator_account', 'beneficiary').order_by('-created_at')
    return render(request, 'bank_transfers/generate_xml.html', {'transfers': transfers})

def upload_excel(request):
    """Excel fájl feltöltése"""
    if request.method == 'POST':
        form = UploadExcelForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            account_number = form.cleaned_data['account_number']
            
            try:
                transfers = parse_excel_file(excel_file, account_number)
                messages.success(request, f'{len(transfers)} utalás sikeresen importálva')
                return redirect('generate_xml_view')
            except Exception as e:
                messages.error(request, f'Hiba az Excel fájl feldolgozása során: {str(e)}')
    else:
        form = UploadExcelForm()
    
    return render(request, 'bank_transfers/upload_excel.html', {'form': form})

