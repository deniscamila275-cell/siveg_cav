"""
================================================================================
CAPA DE VALIDACIÓN Y ENCAPSULAMIENTO EN POO (FORMS)
================================================================================
Define las clases de formulario que encapsulan los controles de entrada de la
interfaz gráfica, los widgets HTML y las reglas de validación de datos.
================================================================================
"""

import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Expediente


# ==============================================================================
# CONCEPTO POO: CLASE DE FORMULARIO (Herencia de forms.ModelForm)
# ==============================================================================
class ReclamoVecinoForm(forms.ModelForm):
    """
    CLASE: ReclamoVecinoForm
    Encapsula la captura y validación de datos del formulario del vecino.
    Hereda de forms.ModelForm, reutilizando la definición de la clase Expediente.
    """

    # CLASE INTERNA (Configuración de metadatos del formulario):
    class Meta:
        model = Expediente  # Clase Modelo vinculada
        fields = ['dni_vecino', 'nombre_completo', 'telefono_contacto', 'detalle_consulta']
        
        # Atributos de Interfaz Gráfica (Widgets HTML / Clases CSS Bootstrap):
        widgets = {
            'dni_vecino': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 36268087',
                'inputmode': 'numeric',
                'pattern': r'^\d{8}$',
                'maxlength': '8',
                'minlength': '8',
                'title': 'DNI de 8 números'
            }),
            'nombre_completo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre y Apellido completo',
                'pattern': r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]{2,}\s+[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]{2,}.*$',
                'title': 'Nombre y apellido completo (solo letras)'
            }),
            'telefono_contacto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 3764187444 o 3764-15-187444',
                'title': 'Teléfono de Posadas/provincia con característica 37'
            }),
            'detalle_consulta': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Escribí tu consulta o reclamo aquí...'
            }),
        }

    def clean_nombre_completo(self):
        nombre = self.cleaned_data.get('nombre_completo', '').strip()
        if not re.fullmatch(r'[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+', nombre):
            raise ValidationError('El nombre y apellido solo debe contener letras.')
        partes = [p for p in nombre.split() if len(p) >= 2]
        if len(partes) < 2:
            raise ValidationError('Por favor, ingresá tu nombre y apellido completo (al menos un nombre y un apellido, ej: Juan Pérez).')
        return nombre

    def clean_dni_vecino(self):
        dni = str(self.cleaned_data.get('dni_vecino', '')).strip()
        if not dni.isdigit():
            raise ValidationError('El DNI solo debe contener números.')
        if len(dni) != 8:
            raise ValidationError('El DNI debe contener exactamente 8 números (sin puntos ni letras, ej: 36268087).')
        return int(dni)

    def clean_telefono_contacto(self):
        telefono_raw = self.cleaned_data.get('telefono_contacto', '').strip()
        if re.search(r'[a-zA-Z]', telefono_raw):
            raise ValidationError('El teléfono de contacto solo debe contener números.')
        digitos = re.sub(r'\D', '', telefono_raw)
        if digitos.startswith('549'):
            digitos = digitos[3:]
        elif digitos.startswith('54'):
            digitos = digitos[2:]
        if digitos.startswith('0'):
            digitos = digitos[1:]
        if not digitos.startswith('37'):
            raise ValidationError('El teléfono debe corresponder a Posadas o la provincia (debe comenzar con la característica 37, ej: 3764187444 o 3764-15-187444).')
        tel_norm = None
        if len(digitos) == 10:
            tel_norm = digitos
        elif len(digitos) == 12 and digitos[4:6] == '15':
            tel_norm = digitos[:4] + digitos[6:]
        elif len(digitos) == 12 and digitos[3:5] == '15':
            tel_norm = digitos[:3] + digitos[5:]
        elif len(digitos) == 11 and (digitos[4:6] == '15' or digitos[3:5] == '15'):
            tel_norm = digitos[:4] + digitos[6:] if digitos[4:6] == '15' else digitos[:3] + digitos[5:]
        if not tel_norm or len(tel_norm) != 10:
            raise ValidationError('El formato del teléfono debe contener la característica 37 y su número (ej: 3764187444 o 3764-15-187444).')
        return tel_norm