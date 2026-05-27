# AutoSocial AI — Developer Guide

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Backend — Django](#backend--django)
   - [Settings](#settings)
   - [URL Routing](#url-routing)
   - [Apps](#apps)
6. [Desktop Agent](#desktop-agent)
   - [Agent Lifecycle](#agent-lifecycle)
   - [WebSocket Protocol](#websocket-protocol)
7. [Browser Automation Engine](#browser-automation-engine)
   - [BrowserManager](#browsermanager)
   - [Task Runner](#task-runner)
   - [Platform Modules](#platform-modules)
8. [Data Flows](#data-flows)
9. [Configuration Reference](#configuration-reference)
10. [Running the Project](#running-the-project)
11. [Key Design Decisions](#key-design-decisions)

---

## Project Overview

AutoSocial AI automates social media posting and comment management across X (Twitter), LinkedIn, Instagram, and Facebook. It consists of a Django REST backend for managing posts/scheduling/comments and a desktop agent that drives a real Chrome browser to perform the actual social media actions.

---

## Architecture

