# Sanep iSim-CS

## Descrição

O projeto é uma aplicação Python que desempenha a gestão de dados provenientes de dispositivos IoT por meio do protocolo MQTT. Ele recebe continuamente dados de sensores, os armazena banco de dados persistente e oferece a capacidade de criar regras de disparo de alertas com a ajuda de um bot integrado.

## Pré-requisitos

- Python 3
- MySQL
- PM2

## Instalação

Para a instalação e execução do projeto basta executar os seguintes comandos:

```
git clone git@github.com:IcaroGSiqueira/sanep.git
ou
git clone https://github.com/IcaroGSiqueira/sanep.git
```

copie o .env.example e o renomeie para .env

preencha as variaveis com os dados a serem usados e em seguida prosiga com os comandos:

```
python3 setup-sanep.py

pm2 start pm2.config.js
```
