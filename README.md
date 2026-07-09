# Kalaivanan K | AI & Robotics Engineer Portfolio

A modern, full-stack personal portfolio and analytics system designed to showcase engineering projects, track viewer engagement, and handle direct communications. 

The project consists of a highly interactive, glassmorphism-styled frontend and a Python (FastAPI) backend that handles custom viewer analytics and data persistence.

## 🚀 Live Demo
**[Insert Your Render URL Here]**

---

## 🧠 System Architecture & How It Works

This project is more than just a static HTML site; it operates with a fully functional backend to gather analytics and manage data.

### 1. The Frontend (UI & Interactions)
* **Visuals:** Built with pure HTML, CSS, and Vanilla JavaScript. It features a dark-mode, sci-fi aesthetic with custom CSS variables, responsive grid layouts, and glassmorphism UI panels.
* **Canvas Particles:** The background features an interactive particle network built using the HTML5 `<canvas>` API and JavaScript requestAnimationFrame, reacting dynamically to screen resizing.
* **Animations:** Uses the `IntersectionObserver` API to trigger smooth, cascading reveal animations as the user scrolls through different sections (Skills, Projects, Experience).
* **3D Tilt Cards:** Project cards utilize a custom JavaScript mouse-tracking script to calculate cursor position and apply a dynamic `rotateX` and `rotateY` CSS transform for a 3D tilt effect.

### 2. The Backend (Viewer Analytics API)
* **Framework:** Powered by **FastAPI** (Python). The server not only serves the static HTML and assets but also exposes RESTful API endpoints (`/api/viewers`, `/api/contact`).
* **Database:** Uses **SQLite3** (`viewer_analytics.db`) to persist data locally.
* **Tracking:** On page load, the frontend silently fires a `POST` request to the backend. The FastAPI server resolves the client's IP address (handling proxy headers from cloud deployments) and logs the viewer's user-agent, screen resolution, timezone, and visit timestamp.

### 3. Contact Form & Email Routing
The contact form utilizes a hybrid approach to ensure reliable delivery bypassing standard cloud-hosting SMTP port blocks:
* **Email Delivery:** The form submits directly to the **Web3Forms API** via a frontend JavaScript `fetch()` call. This allows the system to send emails directly to my Gmail inbox using standard web traffic (Port 443), successfully bypassing the outbound port 587 restrictions commonly enforced by cloud providers.
* **Asynchronous Handling:** The UI updates dynamically based on the API response, providing the user with immediate success/failure feedback without reloading the page.

---

## 🛠️ Technologies Used

**Frontend:**
* HTML5, CSS3, Vanilla JavaScript
* HTML5 Canvas API (Particle rendering)
* Web3Forms API (Email relay)

**Backend & Data:**
* Python 3.11+
* FastAPI (REST API & Static File Serving)
* Uvicorn (ASGI Web Server)
* SQLite3 (Data persistence)
* Pydantic (Data validation)

**Deployment & Version Control:**
* Git & GitHub
* Render (Cloud Web Service Deployment)

---

## 💻 Local Setup & Development

To run this project locally on your machine:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Kalaivanankalai123/portfolio.git](https://github.com/Kalaivanankalai123/portfolio.git)
   cd portfolio
