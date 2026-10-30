# Changelog

Todas as mudanças relevantes deste projeto são registradas aqui.

O formato segue de forma aproximada o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o versionamento segue o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

O projeto reúne duas frentes:

* o **livro** `A Rebeldia da Mecatrônica`, em `capitulos/`;
* a **plataforma Universo Rebeldia**, em `app/`.

---

## [Não lançado] - 2026-10-30

Integração de `eng.caracore.com.br` ao ecossistema Cara Core Informática.

### Adicionado

* Breadcrumb e rodapé legal com CNPJ, contato, Portfólio e Ecossistema no livro
  e no app Universo Rebeldia.
* Selos de maturidade: livro **Disponível** e app **Piloto**.
* Seção "Continue no ecossistema Cara Core" após o Apêndice B e na etapa
  "Criar projeto" do app, com links para Circuito Ferradura, PDV Java,
  Minerador 4.0 e Reino OIDC.
* JSON-LD `Book` e `WebApplication`, Open Graph, canonical e `og:image`.
* Página de créditos no PDF e no HTML, com autoria e publicação.

### Alterado

* Título, descrição, capa e metadados passam a destacar a Cara Core
  Informática; o nome do autor fica nos créditos e nos metadados secundários.
* Favicon do livro passa a usar o ícone do app.
* Cache do service worker atualizado para `v9`.
* Correção de overflow horizontal do layout desktop do livro.

---

## [2.0.0] - 2026-10-14

Lançamento da plataforma Universo Rebeldia, que transforma o livro em uma
experiência interativa offline-first.

### Adicionado

#### Plataforma (Fases 1 a 5)

* PWA instalável com `manifest.json` e service worker cache-first.
* Dashboard de progresso com leitura, conceitos, desafios e projetos.
* Leitor interativo dos 18 capítulos, com busca, favoritos, anotações e
  marcação de leitura.
* Mapa de conceitos navegável com conexões entre temas.
* Enciclopédia local com 18 termos distribuídos em 5 categorias.
* Módulo de desafios com 54 questões entre quizzes e estudos de caso.
* 29 missões e experimentos maker extraídos das seções práticas do livro.
* Gamificação com pontuação, níveis, insígnias e progresso por trilha.
* Laboratório Maker com CRUD de projetos persistidos em IndexedDB.
* Vínculo entre projetos registrados e missões concluídas.
* Timeline tecnológica com 10 marcos entre 1760 e 2030.
* Página de configurações com tema, escala de fonte e redução de movimento.
* Exportação e importação de backup em JSON.
* Funcionamento completo offline após a primeira carga.

#### Pipeline de conteúdo

* `generate_app_data.py` para gerar o índice de capítulos.
* `generate_phase2_data.py` para gerar glossário e mapa de conceitos.
* `generate_phase3_data.py` para gerar desafios, missões e trilhas.
* `publish_site.py` para regenerar dados, compilar o livro e publicar a PWA
  em `docs/app/`.

#### Documentação

* `app/README.md` com arquitetura, fluxos e instruções da plataforma.
* Seção de autoria e originalidade no `README.md`.
* Este `CHANGELOG.md`.

### Alterado

* `compile_html.py` passou a inserir chamadas para a PWA no site oficial.
* `WORKSPACE_MEMORY.md` foi reescrito como guia de onboarding para novas
  pessoas e IAs colaboradoras, incluindo regras técnicas, estado atual,
  limitações conhecidas e prioridades.
* `README.md` passou a documentar a plataforma e o fluxo de publicação.

### Removido

* Dependência de Google Fonts e de qualquer CDN externa no site oficial,
  garantindo a premissa de funcionamento sem rede.

### Corrigido

* Overflow horizontal de 15 px em viewports de 320 px, causado por
  `min-width` no `body`.
* Detalhe da enciclopédia que permanecia vazio quando o termo selecionado
  não pertencia à lista filtrada.
* Barras de progresso das trilhas que não eram atualizadas após a conclusão
  de um desafio.

### Acessibilidade

* Navegação por teclado, foco visível e link para pular ao conteúdo.
* Rótulos ARIA, regiões semânticas e breadcrumbs em todas as telas.
* Alvos de toque com no mínimo 44 px em telas pequenas.
* Suporte a `prefers-reduced-motion`.

---

## [1.2.0] - 2026-08-31

### Adicionado

* Arquivo `CNAME` para publicação no domínio próprio.

### Alterado

* Revisão geral do conteúdo do livro.

---

## [1.1.0] - 2026-06-22

### Alterado

* Capítulo 11 reescrito com foco em sistemas dinâmicos, gargalos de fluxo e
  custo de oportunidade.
* Capítulo 12 reescrito com criptografia assimétrica, integridade encadeada
  e simulação prática de hash.
* Capítulo 13 concluído com o Manifesto do Silício e o continuum tecnológico
  entre o Z80 e os robôs autônomos modernos.
* Capítulo 4 aprimorado com analogias práticas e linha do tempo.

---

## [1.0.0] - 2026-06-18

Primeira versão pública do livro.

### Adicionado

* Estrutura completa dos capítulos sob o padrão editorial.
* `compile_book.py` para geração do PDF A5 diagramado.
* `compile_html.py` para geração do site responsivo mobile-first.
* Publicação em `docs/` via GitHub Pages.
* Ilustrações de capa e de todos os capítulos.
* Apêndice A com glossário de engenharia e automação.
* Apêndice C com a galeria de arte e os prompts de IA utilizados.
* Renderização de fórmulas LaTeX no PDF e no HTML.
* Estética de lousa verde para blocos técnicos e equações.

---

[2.0.0]: https://github.com/chmulato/caracore-eng-mecatronica/compare/75e4c83...HEAD
[1.2.0]: https://github.com/chmulato/caracore-eng-mecatronica/compare/77855aa...75e4c83
[1.1.0]: https://github.com/chmulato/caracore-eng-mecatronica/compare/4a0432e...77855aa
[1.0.0]: https://github.com/chmulato/caracore-eng-mecatronica/commit/4a0432e
