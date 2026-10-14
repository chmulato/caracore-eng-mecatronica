# Universo Rebeldia — Fases 1 a 5

Aplicação web progressiva estática para explorar o livro **A Rebeldia da Mecatrônica**. Esta entrega já cobre:

- Fase 1: estrutura PWA, dashboard e leitor interativo.
- Fase 2: mapa de conceitos e enciclopédia local.
- Fase 3: desafios (quiz, estudos de caso e missões maker), gamificação e persistência dos resultados.
- Fase 4: Laboratório Maker com CRUD de projetos em IndexedDB e vínculo com missões.
- Fase 5: timeline, configurações, backup completo e publicação integrada ao site oficial.

## Árvore de arquivos

```text
app/
├── index.html
├── manifest.json
├── service-worker.js
├── README.md
├── pages/
│   ├── dashboard.html
│   ├── livro.html
│   ├── conceitos.html
│   ├── enciclopedia.html
│   ├── desafios.html
│   ├── laboratorio.html
│   ├── timeline.html
│   └── configuracoes.html
├── assets/
│   ├── css/app.css
│   ├── js/
│   │   ├── app.js
│   │   └── db.js
│   └── icons/icon.svg
├── data/
│   ├── capitulos.json       # gerado; não editar manualmente
│   ├── conceitos.json       # gerado do glossário
│   ├── glossario.json       # gerado do glossário
│   ├── desafios.json        # gerado dos desafios do livro + glossário
│   └── timeline.json        # marcos tecnológicos da plataforma
└── storage/                 # dados do usuário ficam no navegador
```

O script `generate_app_data.py`, na raiz do repositório, transforma os Markdown de `capitulos/` em `app/data/capitulos.json`. O Markdown continua sendo a única fonte de verdade. Execute-o sempre que os capítulos forem alterados:

```powershell
python generate_app_data.py
```

O script `generate_phase2_data.py` transforma o arquivo `capitulos/14_glossario.md` em:

- `app/data/glossario.json` (base local da enciclopédia)
- `app/data/conceitos.json` (categorias e conexões do mapa mental)

Execute-o sempre que o glossário for alterado:

```powershell
python generate_phase2_data.py
```

O script `generate_phase3_data.py` monta o catálogo de desafios em `app/data/desafios.json` a partir de duas fontes do próprio livro:

- as seções `### 🎮 Desafio...` e `### 🔬 Experimento...` dos capítulos viram missões maker e experimentos de campo (um item por nível);
- cada termo do glossário vira três questões objetivas (definição, analogia e aplicação) com alternativas formadas por outros termos reais do livro.

Execute-o depois de `generate_phase2_data.py` e sempre que capítulos ou glossário mudarem:

```powershell
python generate_phase3_data.py
```

## Executar localmente

O service worker e o armazenamento offline exigem `localhost` ou HTTPS. Na raiz do repositório, inicie um servidor estático:

```powershell
python -m http.server 8000
```

Abra `http://localhost:8000/app/`. Depois da primeira carga completa, toda a plataforma fica disponível offline. O aplicativo não usa frameworks, CDN ou dependências externas.

## Publicar o site oficial

O site público é servido a partir de `docs/`. O comando abaixo regenera capítulos, glossário, desafios e o HTML do livro e copia a versão de produção da PWA para `docs/app/`:

```powershell
python publish_site.py
```

Não edite `docs/app/` manualmente. Faça alterações em `app/` e execute novamente o comando de publicação.

## Persistência e comportamento

- Capítulos concluídos, favoritos, anotações, conceitos estudados, respostas, missões e preferências ficam em `localStorage`.
- Projetos maker ficam em IndexedDB, com os campos nome, problema, solução, componentes, resultado esperado, observações e missão relacionada.
- O service worker pré-armazena o shell, todas as páginas e todos os catálogos locais; outras solicitações GET da mesma origem usam cache-first.
- A pesquisa global localiza capítulos, conceitos, missões, projetos e marcos da timeline.
- O progresso de leitura conta capítulos marcados como concluídos; isso não é uma estimativa baseada no scroll.
- O dashboard mostra progresso de leitura, conceitos estudados, desafios concluídos, pontuação e nível atual.
- Mapa de conceitos e enciclopédia reutilizam dados do glossário do livro, sem manter conteúdo duplicado editável no app.

## Desafios e gamificação

- Trilhas: quatro trilhas temáticas de conhecimento (derivadas das categorias do mapa de conceitos) e a trilha "Missões de campo" com os desafios práticos dos capítulos.
- Tipos: `quiz` (5 pontos), `caso` (10 pontos), `missao` (15 pontos no nível 1 e 20 no nível 2) e `experimento` (20 pontos).
- Pontuação é derivada dos itens concluídos, nunca armazenada em separado — o progresso permanece consistente mesmo se o catálogo for regerado.
- Níveis: Aprendiz de bancada, Técnico de campo, Engenheiro rebelde e Mestre da mecatrônica, calculados sobre o total de pontos disponíveis.
- Conquistas: primeiro acerto, dez acertos, cinco estudos de caso, primeira missão, cinco missões e trilha completa. Elas aparecem na arena de desafios e no dashboard.
- Quizzes aceitam novas tentativas; missões guardam um registro textual e podem ser reabertas.

## Laboratório Maker

- Criação, edição, busca e exclusão de projetos locais.
- Vínculo opcional com uma missão maker já concluída.
- Contagem de projetos no dashboard.
- Persistência independente do `localStorage`, adequada a registros maiores e evolução futura.

## Timeline e configurações

- Dez marcos entre 1760 e 2030, com filtros temáticos e atalhos para capítulos relacionados.
- Tema escuro, claro ou do sistema; escala tipográfica de 90% a 125%; redução de movimento.
- Instalação da PWA quando oferecida pelo navegador.
- Exportação e importação de um backup JSON único contendo progresso, preferências e projetos.
- Limpeza explícita de todos os dados locais.

## Próximos passos de evolução

1. Adicionar anexos e imagens aos projetos maker usando blobs no IndexedDB.
2. Criar testes automatizados de navegador para os fluxos críticos.
3. Adicionar sincronização opcional somente quando houver uma API oficial, mantendo o modo local como padrão.
