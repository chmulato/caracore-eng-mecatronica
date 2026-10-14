# Memória do Workspace — A Rebeldia da Mecatrônica

Este documento é o ponto de entrada para qualquer pessoa ou IA que vá colaborar
com o projeto. O repositório é público; não incluir credenciais, tokens,
informações pessoais ou arquivos privados em commits, issues ou documentação.

**Repositório:** <https://github.com/chmulato/livro_eng_mecatronica>

**Site oficial:** <https://eng.caracore.com.br/>

**PWA publicada:** <https://eng.caracore.com.br/app/>

---

## 1. Missão do projeto

`A Rebeldia da Mecatrônica` é um romance instrutivo sobre tecnologia,
engenharia, autonomia e sociedade. O projeto digital amplia o livro por meio
do **Universo Rebeldia**, uma PWA educacional offline-first para estudantes,
makers, técnicos, engenheiros, professores, empreendedores e leitores.

O objetivo não é substituir o livro. O objetivo é levar o leitor de:

1. leitura;
2. compreensão dos conceitos;
3. prática guiada;
4. criação e registro de projetos;
5. reflexão crítica sobre tecnologia.

O tom deve ser conversacional, prático, motivador e instigante. Matemática,
computação de baixo nível e automação devem ser apresentadas como ferramentas
para compreender e transformar o mundo real, não como decoreba.

---

## 2. Estado atual

Último marco publicado:

- **Commit:** `b3497d3` — `Adiciona plataforma PWA Universo Rebeldia`
- **Branch principal:** `master`
- **GitHub Pages:** configurado para publicar a partir de `master:/docs`
- **Service worker da PWA:** cache `universo-rebeldia-v6`
- **Status:** fases 1 a 5 implementadas e publicadas

Funcionalidades disponíveis:

- leitor interativo com 18 capítulos;
- busca, favoritos, anotações e marcação de leitura;
- dashboard de progresso;
- mapa de conceitos;
- enciclopédia local;
- 54 desafios entre quizzes e estudos de caso;
- 29 missões e experimentos maker;
- pontuação, níveis, trilhas e conquistas;
- Laboratório Maker com CRUD de projetos;
- persistência de projetos em IndexedDB;
- timeline tecnológica com 10 marcos;
- tema claro/escuro, escala de fonte e redução de movimento;
- instalação da PWA;
- exportação e importação de backup JSON;
- funcionamento offline;
- integração do site oficial com a PWA;
- layout mobile-first validado em viewport de 320 px.

Débitos conhecidos:

- não há suíte automatizada formal nem CI dedicada;
- `app/assets/js/app.js` concentra muitas responsabilidades e deve ser
  modularizado com cuidado;
- ainda faltam simuladores educacionais;
- os desafios precisam de formatos mais variados para evitar repetição;
- o Laboratório Maker pode evoluir para projetos guiados, evidências e
  rubricas;
- o progresso é local ao dispositivo, sem sincronização entre usuários;
- a atualização de cache do service worker deve ser testada após cada release;
- é recomendável medir Lighthouse e testar em aparelhos físicos.

---

## 3. Arquitetura do repositório

### Livro

- `capitulos/`: fonte única de verdade do conteúdo em Markdown.
- `imagens/`: capa e ilustrações do livro.
- `compile_book.py`: compila o PDF diagramado.
- `compile_html.py`: converte os capítulos para o site HTML.
- `docs/`: artefatos publicados no GitHub Pages.

### Aplicação

- `app/index.html`: shell da PWA.
- `app/pages/`: páginas carregadas pelo roteador hash.
- `app/assets/css/app.css`: estilos, temas, acessibilidade e breakpoints.
- `app/assets/js/app.js`: estado, roteamento, renderização e interações.
- `app/assets/js/db.js`: wrapper IndexedDB do Laboratório Maker.
- `app/data/`: dados gerados para capítulos, conceitos, desafios e timeline.
- `app/manifest.json`: manifesto instalável.
- `app/service-worker.js`: cache-first e recursos offline.
- `app/storage/`: reservado para organização local; não guardar dados de
  usuários no Git.

### Dados e publicação

- `generate_app_data.py`: gera `capitulos.json` a partir de `capitulos/*.md`.
- `generate_phase2_data.py`: gera conceitos, glossário e enciclopédia.
- `generate_phase3_data.py`: gera desafios, missões e trilhas.
- `publish_site.py`: executa os geradores, compila o site e copia `app/` para
  `docs/app/`.
- `docs/app/`: cópia de produção da PWA; não editar manualmente.

---

## 4. Regras técnicas

1. Usar somente HTML5, CSS3, JavaScript ES6+, Python e APIs nativas do
   navegador.
2. Não adicionar React, Vue, Angular, bundlers, CDNs ou dependências externas
   de execução.
3. O livro em Markdown permanece como fonte única de verdade. Não duplicar
   capítulos manualmente em JSON ou HTML.
4. Toda funcionalidade principal deve funcionar sem internet depois do
   primeiro carregamento.
5. Preferir `localStorage` para estado leve e `IndexedDB` para projetos ou
   dados estruturados.
6. Manter navegação por teclado, foco visível, contraste adequado, rótulos
   ARIA e alvos de toque de pelo menos 44 px.
7. Validar mudanças em desktop e em viewport de 320 px antes de publicar.
8. Atualizar o nome do cache no service worker quando houver alteração que
   exija invalidação explícita.
9. Não editar `docs/app/` manualmente; regenerar com o pipeline.
10. Não apagar ou reverter alterações de outras pessoas sem entender sua
    origem.

---

## 5. Fluxo recomendado para uma IA colaboradora

Antes de editar:

```bash
git status --short
git log --oneline -5
```

Leia esta memória, o `README.md` correspondente à área alterada e os arquivos
de origem relacionados. Procure implementações existentes antes de criar novos
helpers ou padrões.

Após alterar o livro:

```bash
python publish_site.py
```

Após alterar somente a PWA, ainda é recomendável executar o mesmo pipeline para
manter `app/` e `docs/app/` idênticos.

Validações mínimas:

```bash
python -m json.tool app/data/capitulos.json > $null
python -m json.tool app/data/conceitos.json > $null
python -m json.tool app/data/desafios.json > $null
python -m json.tool app/data/timeline.json > $null
node --check app/assets/js/app.js
git diff --check
```

Para publicar:

```bash
git add -A
git commit -m "Mensagem descritiva"
git push origin master
```

O commit deve explicar a intenção da alteração. Não usar `--force`, não
ignorar hooks e não incluir arquivos temporários, caches de navegador ou
segredos.

---

## 6. Diretrizes editoriais

- Preservar o continuum entre o Z80, a eletrônica de baixo nível e os robôs
  autônomos modernos com ROS 2 e SLAM.
- Explicar sistemas complexos por analogias concretas, sem perder precisão.
- Manter a conexão entre tecnologia, autonomia, soberania e responsabilidade
  social.
- Evitar glorificar a tecnologia como solução automática para problemas
  humanos ou sociais.
- Ao inserir uma seção didática, incluir contexto, exemplo prático e uma forma
  de o leitor testar ou questionar a ideia.
- No PDF, preservar proporção nativa das imagens usando cálculo dinâmico com
  Pillow.
- Manter o recuo nulo no primeiro parágrafo após cabeçalhos, imagens, lousas,
  códigos ou caixas especiais; parágrafos narrativos subsequentes usam o
  recuo literário padrão.
- Preservar as transições suaves e o espaço para o cabeçalho fixo no HTML.

---

## 7. Próximas evoluções prioritárias

1. Remover referências visíveis a “Fase 1–5” da experiência final do usuário.
2. Adicionar onboarding por perfil de público.
3. Criar simuladores nativos de portas lógicas, registradores, controle e
   robótica.
4. Diversificar desafios com diagnóstico de falhas, diagramas, cálculos e
   decisões de projeto.
5. Transformar o Laboratório Maker em caderno de engenharia com etapas,
   medições, evidências e conclusão.
6. Conectar missões aos personagens, capítulos e acontecimentos da narrativa.
7. Criar modo professor com trilhas e relatórios, sem comprometer o modo
   offline.
8. Adicionar testes automatizados para geradores, dados e fluxos críticos.
9. Medir Lighthouse e validar em Android e iOS reais.

Qualquer nova IA deve atualizar esta memória quando uma decisão arquitetural
importante, uma limitação relevante ou um novo fluxo de colaboração for
descoberto.
