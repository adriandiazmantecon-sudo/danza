import re
import unicodedata

def clean_company(company):
    # Regex from paco_rabal.py
    company = re.sub(r'^(?:Compañía|Cía\.?|Cia\.?|Profesora?|Director|Coreografía|Dirección|Autora?|Conservatorio|Grupo):\s*', '', company, flags=re.IGNORECASE)
    return company

# Test with various encodings of 'ñ'
test_str = "Compañía Elías Aguirre"
print(f"Original: {test_str}")
print(f"Cleaned: {clean_company(test_str)}")

# Test with NFC/NFD
nfd_str = unicodedata.normalize('NFD', test_str)
print(f"NFD Cleaned: {clean_company(nfd_str)}")

# Test with the specific characters we saw
chars = [ord(c) for c in test_str]
print(f"Chars: {chars}")
