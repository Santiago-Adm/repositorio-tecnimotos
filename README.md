# 🏍️ Tecnimotos Santi

[![Last Commit](https://img.shields.io/github/last-commit/Santiago-Adm/repositorio-tecnimotos)](https://github.com/Santiago-Adm/repositorio-tecnimotos/commits/main)
[![Code Size](https://img.shields.io/github/languages/code-size/Santiago-Adm/repositorio-tecnimotos)](https://github.com/Santiago-Adm/repositorio-tecnimotos)
[![Top Language](https://img.shields.io/github/languages/top/Santiago-Adm/repositorio-tecnimotos)](https://github.com/Santiago-Adm/repositorio-tecnimotos)
[![Issues](https://img.shields.io/github/issues/Santiago-Adm/repositorio-tecnimotos)](https://github.com/Santiago-Adm/repositorio-tecnimotos/issues)
[![Stars](https://img.shields.io/github/stars/Santiago-Adm/repositorio-tecnimotos)](https://github.com/Santiago-Adm/repositorio-tecnimotos/stargazers)

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)

## 📖 Sobre el Proyecto

**Tecnimotos Santi** es un sistema de gestión operativa integral diseñado
para digitalizar el ciclo completo de una tienda y taller autorizado Bajaj
y TVS en Ayacucho, Perú: catálogo de repuestos, pedidos de clientes,
órdenes de trabajo del taller y control de stock, con roles diferenciados
para personal interno (administración, ventas, mecánica) y clientes
externos (conductores de mototaxi, distritos y zona rural).

### 🎯 Objetivo General

Modernizar la operación diaria de Tecnimotos Santi reemplazando procesos
manuales y dispersos por una plataforma única, segura y trazable —
reduciendo tiempos de atención al cliente, dando visibilidad en tiempo real
del stock y del avance de cada orden de trabajo, y sentando una base técnica
sólida (arquitectura hexagonal, autenticación robusta, cifrado de datos
sensibles) sobre la cual crecer sin reescribir el sistema desde cero.

## Arquitectura

- **Backend**: Python / FastAPI, Modular Monolith con Arquitectura
  Hexagonal (dominio, aplicación e infraestructura separados por módulo:
  `catalogo`, `pedidos`, `taller`, `stock`, `shared`).
- **Frontend**: Next.js 14 (App Router), React, Tailwind CSS.
- **Persistencia**: PostgreSQL (async, SQLAlchemy + Alembic) y Redis
  (sesiones, rate-limiting).
- **Almacenamiento de archivos**: Cloudflare R2 (imágenes de repuestos,
  comprobantes de pago).
- **Autenticación**: JWT (RS256) con doble factor por correo para roles
  administrativos, contraseñas con Argon2id, cifrado en reposo de datos
  sensibles.

## Estado del proyecto

En despliegue activo. El desarrollo sigue un protocolo documentado de
"piezas" (auditoría de seguridad, pulido de interfaz, verificación end-to-end
y despliegue) antes de cada publicación a producción.

## Despliegue

Backend en [Railway](https://railway.app) (API + PostgreSQL + Redis),
frontend en [Vercel](https://vercel.com).

URL de producción: **https://repositorio-tecnimotos.vercel.app**

## Documentación interna

El protocolo de construcción, decisiones de arquitectura y checklists
operativos para agentes/CLI viven en `.doc3/` (no incluido en este
repositorio — documentación privada del equipo). Este repositorio no
contiene datos reales de clientes ni credenciales.
