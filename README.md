# A Rebeldia da Mecatrônica

📖 **Leia o livro online:** [A Rebeldia da Mecatrônica](https://eng.caracore.com.br/)

Este repositório contém o código-fonte, capítulos e scripts de compilação do livro **A Rebeldia da Mecatrônica - Romance Instrutivo de Tecnologia e Sociedade**.

## Estrutura do Repositório

* `/capitulos/`: Arquivos Markdown de cada um dos 13 capítulos estruturados sob o Padrão Editorial.
* `compile_book.py`: Script Python para geração do livro em formato PDF A5 com fonte Verdana 12 e leading condensado.
* `compile_html.py`: Script Python para compilação em página única HTML responsiva Mobile-First.
* `foundation.md`: Documento de fundação com a bíblia de personagens e diretrizes originais.
* `padrao_editorial.md`: Guia de estilo, ritmo e estrutura de escrita adotada no livro.
* `romance_instrutivo.pdf`: Livro compilado pronto em formato PDF.
* `romance_instrutivo.html`: Livro compilado pronto em formato HTML responsivo.

## Requisitos de Compilação

Para compilar o livro localmente, instale o ReportLab:

```bash
pip install reportlab
```

E execute:

```bash
python compile_book.py
python compile_html.py
```

## Universo Rebeldia (PWA)

O aplicativo está em `app/` e prioriza **Ler → Refletir → Conectar Conceitos → Criar Projeto**, com experiência mobile e funcionamento offline após o primeiro carregamento completo. Reflexões e rascunhos são salvos localmente; projetos preservam o capítulo, os conceitos conectados e um primeiro teste verificável. Não há gamificação, rankings ou certificações no fluxo ativo. Todo o conteúdo do livro publicado no PWA é gerado a partir dos Markdown originais em `capitulos/`; não edite manualmente o JSON gerado.

Atualize o índice do aplicativo sempre que alterar um capítulo:

```bash
python generate_app_data.py
```

Para a Fase 2 (mapa de conceitos e enciclopédia), gere os dados locais a partir do glossário:

```bash
python generate_phase2_data.py
```

Os projetos ficam em IndexedDB; Configurações permite instalar a PWA e exportar/importar dados. Os recursos secundários de fases anteriores estão fora da navegação e suas rotas foram desativadas, preservando dados existentes. Para gerar os dados, compilar o livro e publicar a PWA em `docs/app/`, execute:

```bash
python publish_site.py
```

Para testar localmente (service workers exigem `localhost` ou HTTPS), execute na raiz do repositório:

```bash
python -m http.server 8000
```

Depois acesse `http://localhost:8000/app/` durante o desenvolvimento ou `http://localhost:8000/docs/` para validar exatamente a estrutura publicada no GitHub Pages. A arquitetura e os fluxos estão documentados em [`app/README.md`](app/README.md).

## Autoria e Originalidade

A obra e a plataforma são de autoria de **Christian Vladimir Uhdre Mulato**.

### O que é original neste projeto

* **Narrativa:** personagens, enredo, diálogos e ambientação são criação autoral, com as diretrizes originais documentadas em [`foundation.md`](foundation.md).
* **Código:** a PWA em `app/` foi escrita do zero em HTML5, CSS3 e JavaScript ES6+, sem frameworks, sem bibliotecas de terceiros e sem CDNs. Não há código importado que exija atribuição ou licença externa.
* **Identidade visual:** paleta, logotipo, composição e estética tech-noir industrial foram definidas especificamente para esta obra.
* **Arquitetura de conteúdo:** o pipeline que transforma `capitulos/*.md` em enciclopédia, mapa de conceitos, desafios e trilhas é próprio do projeto. O livro é a fonte única de verdade e o conteúdo derivado não é duplicado manualmente.

### Sobre o uso de Inteligência Artificial

Ferramentas de IA foram utilizadas como apoio na implementação, revisão e geração de ilustrações. Isso é declarado abertamente, em coerência com a proposta do livro de "abrir a caixa preta" — os prompts de arte estão documentados no Apêndice C ([`capitulos/16_galeria_arte.md`](capitulos/16_galeria_arte.md)).

A direção autoral permanece humana. As decisões sobre propósito, público, mensagem, escopo, aceitação ou rejeição de sugestões e o significado atribuído ao conjunto são do autor.

Nenhuma criação parte do zero absoluto: toda obra se apoia em linguagem, técnicas e referências anteriores. Originalidade aqui não significa ausência de influências, e sim a transformação dessas influências em uma expressão com identidade própria. Livros interativos, gamificação, PWAs e laboratórios maker já existiam isoladamente; a combinação específica em torno do universo de *A Rebeldia da Mecatrônica* é que constitui a obra.

O histórico completo de evolução está em [`CHANGELOG.md`](CHANGELOG.md).
