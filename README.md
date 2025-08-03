# 🛎️ WorldHotels – Hotel Booking System

WorldHotels is a full-stack web application built using Flask and MySQL, designed to simulate a hotel booking system with both user and admin roles.

---

## 📦 Features

- User registration and login (with hashed passwords)
- Admin and user role-based access
- Hotel and room management (admin)
- Booking system with early-bird discounts
- Admin dashboard for managing bookings and users
- Containerized using Docker and Docker Compose

---
### UI Preview

**Booking Main Page:**

<img width="1407" height="791" alt="Booking Main Page" src="https://github.com/user-attachments/assets/7f7afdc7-edde-4ca6-9062-4ed994fc0a55" />


---

## 🛠 Requirements

Install the following **before running the project**(if you don't already have installed):

- [Docker](https://www.docker.com/products/docker-desktop)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/)

---

## 🧪 Test Accounts

| Role  | Username     | Password     |
|-------|--------------|--------------|
| Admin | `testAdmin` | `testAdmin`  |
| User  | `testUser`  | `testUser`   |

---

## 🚀 Getting Started

### 📁 Step 1: Clone the Repository

```bash
git clone https://github.com/mohameda-li/WorldHotels.git
cd WorldHotels/Project
```


---

### 🧾 Step 2: Create a .env File

Inside the `Project` folder, create a `.env` file and add the following content:

```env
DB_HOST=db
DB_USER=admin_user
DB_PASSWORD=admin_pass
DB_NAME=WorldHotels
SECRET_KEY=yourflasksecret
```

### 🐳 Step 3: Start the App with Docker

Make sure you're still inside the `Project` folder, then run:

```bash
docker-compose up --build
```

### 🌐 Step 4: Open the App in Your Browser

Once the containers are running, go to:

```url
http://localhost:5001
```

### 📂 Project Structure

```plaintext
WorldHotels/
├── README.md
└── Project/
    ├── app.py
    ├── config.py
    ├── db.py
    ├── utils.py
    ├── docker-compose.yml
    ├── Dockerfile
    ├── requirements.txt
    ├── routes/
    ├── templates/
    ├── static/
    └── docker_sql/
```
