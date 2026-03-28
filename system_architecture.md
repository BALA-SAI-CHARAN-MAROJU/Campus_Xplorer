# Campus Explorer System Architecture and Documentation

## 1. Directory Structure

Below is an overview of the key folders in the project directory and their purposes:
- **`app/`**: The core application package containing all modular code, endpoints, models, and services.
  - **`admin/`**: Flask Blueprint directory for administration functionality (admin dashboard, user roles, management views).
  - **`api/`**: Flask Blueprint directory for REST API endpoints required by the frontend scripts (e.g., fetching campus data, events).
  - **`auth/`**: Flask Blueprint directory for handling user authentication routes (Google OAuth integration, session management, logout).
  - **`main/`**: Flask Blueprint directory containing the core user-facing routes (homepage, maps, user dashboards).
  - **`services/`**: Contains business logic and external integrations (e.g., `groq_chat.py` for AI integration, Maps API integrations).
- **`instance/`**: Contains environment-specific configurations and the default SQLite database file (`campus_explorer.db`).
- **`migrations/`**: Managed by Flask-Migrate (Alembic) to keep track of database schema changes and handle versioned database upgrades/downgrades.
- **`static/`**: Holds statically served web assets such as CSS stylesheets, JavaScript client-side bundles, and images.
- **`templates/`**: Contains Jinja2 HTML templates rendered on the server side to build the dynamic web pages.
- **`tests/`**: Contains unit and integration test suites executed by `pytest` to ensure application stability.

---

## 2. System Design

The application works on a **Client-Server Architecture** primarily using the **Model-View-Controller (MVC)** design pattern constructed with Python's **Flask** framework. 

- **Application Factory Pattern**: The app is initialized using a factory function (`create_app` inside `app/__init__.py`). This allows multiple app instances with distinct configurations (Development, Production, Testing) to coexist and scale easily.
- **Modular Routes (Blueprints)**: To avoid monolithic routing, the application divides code into logically separated 'Blueprints' (`auth`, `main`, `admin`, `api`). This structures views natively along application domains.
- **Dynamic Frontend**: Views are rendered progressively through Jinja2 server-side templating but utilize Javascript heavily on the client (e.g., rendering dynamic Maps integrations and asynchronous API interactions).
- **Service Layer**: External interactions (Large Language Models through Groq/OpenAI, Google Login, Map APIs) are abstracted into the `app/services` directory to separate external API concerns from the primary web routing logic.

---

## 3. Database & Architecture

### Database Used
The application defaults to an **SQLite** database, designated by `sqlite:///campus_explorer.db` within the configuration. Interaction with this database is performed via an Object Relational Mapper (**Flask-SQLAlchemy** module), which abstracts basic SQL into Python objects. Because of SQLAlchemy, the database can easily be scaled vertically to PostgreSQL or MySQL simply by declaring a standard `DATABASE_URL` environment variable.

### Database Architecture & Table Schema 

The relational database involves the following key models representing our table schema:

1. **`users` Table**: Handles user profiles and authorization contexts.
   - `id`: String (PK, UUID format)
   - `google_id`: String (Unique)
   - `email`: String (Unique)
   - `name`: String
   - `profile_picture`: String (URL)
   - `is_admin`: Boolean
   - `is_manager`: Boolean
   - `preferred_campus`: String
   - `theme_preference`: String
   - `created_at`: DateTime
   - `last_login`: DateTime
   - *Relationships*: Links to `events` (one-to-many) and `conversations` (one-to-many).

2. **`events` Table**: Campus events details and scheduling.
   - `id`: Integer (PK)
   - `name`: String
   - `description`: Text
   - `venue_name`: String
   - `campus_id`: String
   - `date`: Date
   - `start_time`: Time
   - `end_time`: Time
   - `created_by`: String (Foreign Key resolving to `users.id`)
   - `created_at`: DateTime
   - `updated_at`: DateTime
   - `is_active`: Boolean

3. **`campuses` Table**: Multi-campus geographical contexts.
   - `id`: String (PK)
   - `name`: String
   - `display_name`: String
   - `center_latitude`: Float
   - `center_longitude`: Float
   - `locations_data`: JSON (stores rich boundary and pin coordinate maps)
   - `map_bounds`: JSON
   - `timezone`: String
   - `is_active`: Boolean
   - `created_at`: DateTime

4. **`conversations` Table**: Storage structure caching historical AI chat logs per user.
   - `id`: String (PK, UUID)
   - `user_id`: String (Foreign Key resolving to `users.id`)
   - `campus_context`: String
   - `messages`: JSON (The raw conversation array between the agent and user)
   - `created_at`: DateTime
   - `updated_at`: DateTime

---

## 4. Main Function Names & Their Purposes

### Core Entry Point (`run.py` & `app/__init__.py`)
- **`create_app(config_name)`** *(app/\_\_init\_\_.py)*: The central function to piece together the entire application. It executes the Application Factory pattern logic to load configuration variables into Flask, bind extensions (SQLAlchemy, LoginManager, Migrate), and sequentially register backend Blueprints.
- **`make_shell_context()`** *(run.py)*: Registers a Flask CLI processor function allowing developers to drop into `flask shell` with a preloaded dictionary of application data models (User, Event, Campus, Conversation) and the active `db` object session.
- **`init_db()`** *(run.py)*: Bound as a Flask CLI command (`flask init_db`). It invokes `db.create_all()` which provisions the immediate table schema directly to the configured dialect upon setting up the project locally.
- **`create_admin()`** *(run.py)*: Setup script tied to Flask CLI to initialize an emergency administrator user for systems bootstrapping.
