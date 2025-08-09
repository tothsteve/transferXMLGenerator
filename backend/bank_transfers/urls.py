from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create_transfer, name='create_transfer'),
    path('beneficiaries/', views.beneficiaries, name='beneficiaries'),
    path('accounts/', views.accounts, name='accounts'),
    path('generate-xml/', views.generate_xml_view, name='generate_xml_view'),
    path('upload-excel/', views.upload_excel, name='upload_excel'),
]
