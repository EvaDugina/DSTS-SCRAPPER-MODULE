CREATE TABLE articles	(
	id serial,
	article_name text, -- --> название артукула с пробелом
	producer_id integer, -- --> идентификатор производителя
	CONSTRAINT articles_pkey PRIMARY KEY (id)
);

CREATE TABLE articles_comparison ( -- таблица кросс-референса артикулов
	id serial,
	first_article_id integer, -- --> идентификатор артукула
	second_article_id integer, -- --> идентификатор артукула
	CONSTRAINT articles_comparison_pkey PRIMARY KEY (id)
);

CREATE TABLE producer_name_variations ( -- таблица альтернативных наименований артикула
	id serial,
	producer_id integer, -- --> идентификатор производителя
	producer_name text, -- --> навзание производителя
	CONSTRAINT producer_name_variations_pkey PRIMARY KEY (id)
);

CREATE TABLE producers	(
	id serial,
	producer_name text UNIQUE, -- --> название производителя
	CONSTRAINT producers_pkey PRIMARY KEY (id)
);
