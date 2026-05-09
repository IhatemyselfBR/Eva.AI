def ajustar_peso(memoria, chave, valor):
    if chave not in memoria or not isinstance(memoria[chave], dict):
        return False, "Alvo inválido ou não encontrado", False
    if 'peso' not in memoria[chave]:
        memoria[chave]['peso'] = 1
    memoria[chave]['peso'] += valor

    # CORREÇÃO: limite inferior em -1
    if memoria[chave]['peso'] < -1:
        memoria[chave]['peso'] = -1

    np = memoria[chave]['peso']
    if np <= 0:
        return True, f"Rank crítico ({np}). Vou buscar outro.", True
    return True, f"Rank atualizado: {np}", False

def validar_memoria(memoria, chave):
    if chave in memoria and isinstance(memoria[chave], dict):
        return memoria[chave].get('peso', 0) > 0
    return False
