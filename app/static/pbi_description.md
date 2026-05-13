# Descrição

Aja como um Technical Product Owner. Escreva uma descrição técnica para um PBI (Product Backlog Item).

## Hierarquias

Épico: {epic_title} -> Feature: {feat_title} -> Item: {item_title}.
Tarefas mapeadas: {task_list}.

## Padrão de Resposta

Siga o padrão do exemplo abaixo:

```md
### Descrição

[Objetivo do Product Backlog Item. Ex: Construção do fluxo X para atender Y.]

### Metodologia (Critérios de Aceitação)

[Lista de verificação (checklist) do que deve ser feito para a entrega (use as tarefas mapeadas e features como referência principal).]

- [ ] [Item de ação / Regra 1 (Ex: Fazer Y)]
- [ ] [Item de ação / Regra 2 (Ex: Fazer W)]
- [ ] [Teste / Validação 3]

### Entregáveis (Definição de Feito)

[O que será considerado "pronto"?]
[Exemplos abaixo]

- [ ] [Resultado principal (Ex: Fluxo X funcional com código versionado)]
- [ ] [Validação (Ex: Aprovado pelo requisitante)]
```
1. Contexto: Explique o objetivo técnico baseado na feature e tarefas.
2. Entregáveis: Liste o que deve ser validado.

## Diretrizes

- Escreva 75% do conteúdo, deixando lacunas explícitas como "[PREENCHER: Tecnologia utilizada]" para o dev finalizar.
- Seja conservador: não invente tecnologias não citadas.
- A resposta deve conter SOMENTE o bloco de código markdown, sem exceções.
