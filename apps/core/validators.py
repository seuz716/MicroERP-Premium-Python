"""
Validators - Validadores reutilizables para MicroERP.
Todos los validadores son métodos estáticos que retornan booleanos o lanzan excepciones.
"""
import re
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError


class Validators:
    """
    Conjunto de validadores para el sistema MicroERP.
    Uso: Validators.is_valid_id(value)
    """
    
    # Patrones regex
    ID_PATTERN = re.compile(r'^[A-Z0-9_-]{3,20}$')
    NAME_PATTERN = re.compile(r'^[\w\s\-ñÑáéíóúÁÉÍÓÚ]{1,100}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?[\d\s\-()]{8,20}$')
    
    @staticmethod
    def is_valid_id(val: str) -> bool:
        """
        Valida un ID con formato: 3-20 caracteres alfanuméricos, guiones o underscores.
        Ejemplos válidos: PROD_001, CLI-123, ABC123
        """
        if not val or not isinstance(val, str):
            return False
        return bool(Validators.ID_PATTERN.match(val))
    
    @staticmethod
    def is_valid_price(val) -> bool:
        """
        Valida un precio: 0 a 999,999.99
        Acepta int, float, Decimal o string numérico.
        """
        try:
            price = Decimal(str(val))
            return Decimal('0') <= price <= Decimal('999999.99')
        except (InvalidOperation, ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_stock(val) -> bool:
        """
        Valida cantidad de stock: 0 a 99,999
        """
        try:
            stock = int(val)
            return 0 <= stock <= 99999
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_name(val: str) -> bool:
        """
        Valida un nombre: 1-100 caracteres, permite letras, números, espacios y símbolos básicos.
        """
        if not val or not isinstance(val, str):
            return False
        return bool(Validators.NAME_PATTERN.match(val.strip()))
    
    @staticmethod
    def is_valid_email(val: str) -> bool:
        """Valida un email."""
        if not val or not isinstance(val, str):
            return False
        return bool(Validators.EMAIL_PATTERN.match(val))
    
    @staticmethod
    def is_valid_phone(val: str) -> bool:
        """Valida un número de teléfono."""
        if not val or not isinstance(val, str):
            return False
        return bool(Validators.PHONE_PATTERN.match(val))
    
    @staticmethod
    def is_valid_quantity(val) -> bool:
        """
        Valida una cantidad positiva: 1 a 99,999
        """
        try:
            qty = int(val)
            return 1 <= qty <= 99999
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_percentage(val) -> bool:
        """Valida un porcentaje: 0 a 100."""
        try:
            pct = Decimal(str(val))
            return Decimal('0') <= pct <= Decimal('100')
        except (InvalidOperation, ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_id(val: str, field_name: str = 'ID'):
        """
        Valida un ID y lanza ValidationError si es inválido.
        """
        if not Validators.is_valid_id(val):
            raise ValidationError(
                f'{field_name} debe tener 3-20 caracteres alfanuméricos (ej: PROD_001)'
            )
        return val
    
    @staticmethod
    def validate_price(val, field_name: str = 'Precio') -> Decimal:
        """
        Valida un precio y retorna como Decimal.
        Lanza ValidationError si es inválido.
        """
        try:
            price = Decimal(str(val))
            if not Validators.is_valid_price(price):
                raise ValidationError(
                    f'{field_name} debe estar entre 0 y 999,999.99'
                )
            return price
        except (InvalidOperation, ValueError, TypeError):
            raise ValidationError(f'{field_name} debe ser un valor numérico válido')
    
    @staticmethod
    def validate_stock(val, field_name: str = 'Stock') -> int:
        """
        Valida stock y retorna como int.
        Lanza ValidationError si es inválido.
        """
        try:
            stock = int(val)
            if not Validators.is_valid_stock(stock):
                raise ValidationError(
                    f'{field_name} debe estar entre 0 y 99,999'
                )
            return stock
        except (ValueError, TypeError):
            raise ValidationError(f'{field_name} debe ser un número entero válido')
    
    @staticmethod
    def validate_name(val: str, field_name: str = 'Nombre') -> str:
        """
        Valida un nombre y retorna limpio.
        Lanza ValidationError si es inválido.
        """
        if not val or not isinstance(val, str):
            raise ValidationError(f'{field_name} es requerido')
        
        val = val.strip()
        if not Validators.is_valid_name(val):
            raise ValidationError(
                f'{field_name} debe tener 1-100 caracteres válidos'
            )
        return val
