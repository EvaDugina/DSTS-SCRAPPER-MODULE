CREATE TABLE articles	(
	id serial,
	article_name text, -- --> название артукула с пробелами
	producer_id integer, -- --> идентификатор производителя
	CONSTRAINT articles_pkey PRIMARY KEY (id)
);

CREATE TABLE producers ( -- таблица наименований производителя
	id serial, -- --> идентификатор производителя
	producer_name text, -- --> навзание производителя c пробелами
	CONSTRAINT producers_pkey PRIMARY KEY (id)
);

CREATE TABLE articles_comparison ( -- таблица кросс-референса артикулов
	id serial,
	group_id integer, -- --> идентификатор группы аналогов
	article_id integer, -- --> идентификатор артукула
	catalogue_name text, -- --> название каталога, установившего аналог
	CONSTRAINT articles_comparison_pkey PRIMARY KEY (id)
);

CREATE TABLE producers_name_variations ( -- таблица альтернативных наименований артикула
	id serial,
	producer_id integer, -- --> идентификатор производителя
	producer_name text, -- --> навзание производителя
	catalogue_name text, -- --> название каталога, для которого актуальна данная вариация
	CONSTRAINT producer_name_variations_pkey PRIMARY KEY (id)
);

CREATE TABLE articles_details ( -- таблица информации о товаре
	id serial,
	article_id integer, -- --> идентификатор артикула
	catalogue_name text, -- --> навзание каталога, из которого взята информация
	json text, -- --> строка информации в формате json
	CONSTRAINT articles_details_pkey PRIMARY KEY (id)
);

CREATE TABLE producers_dsts_names	(
	id serial,
	producer_name text UNIQUE, -- --> название производителя в системе ДСТС
	CONSTRAINT producers_dsts_name_pkey PRIMARY KEY (id)
);


