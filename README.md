
<img width="203" height="193" alt="Logo_1_0 25" src="https://github.com/user-attachments/assets/96f8f633-7e33-473e-9571-b916b6c70670" />
  
  
  
  
Welcome to UniTrade！  
Possibly the (future) greatest student-to-student marketplace!

---

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-323330?style=for-the-badge&logo=javascript&logoColor=F7DF1E)
![MySQL](https://img.shields.io/badge/MySQL-005C84?style=for-the-badge&logo=mysql&logoColor=white)


### Core Features

* **Role-Based Access Control:** Custom registration system allowing users to sign up as either a "Student" (Buyer) or a "Merchant" (Seller) with dedicated dashboards.
* **Real-Time Messaging:** Integrated chat system with dynamic "Online/Offline" status and automated JS polling to facilitate easy communication between buyers and sellers.
* **Live AJAX Search:** Instantly updates product results in a dropdown as the user types, without reloading the page.
* **Safe Concurrency Checkout:** Utilizes database locking (`select_for_update()`) to prevent race conditions (e.g., two users buying the last item simultaneously), ensuring exact stock deduction.
* **Sustainable & Accessible Design:** Fully responsive UI built with CSS Flexbox/Grid. Optimized for performance with WebP image conversion, achieving a 95+ Google Lighthouse performance score. Fully navigable via keyboard with comprehensive screen-reader support.
* **Academic Email Verification:** Registration is strictly limited to valid student email addresses (ending in .ac.uk). A verification code is sent to the user's inbox, and successful verification is required before they can log in.

### Tech Stack

* **Front-end:** HTML5, CSS3, Vanilla JavaScript (AJAX)
* **Back-end:** Python, Django Framework
* **Database:** MySQL (AWS RDS for deployment)
* **Deployment:** Nginx (Reverse Proxy), Gunicorn, Certbot (HTTPS)

### Local Setup

##### Installation

1. **Clone the repo**
    ```sh
    git clone [https://github.com/BaselAbuRamadan/UniTrade.git](https://github.com/BaselAbuRamadan/UniTrade.git)
    cd UniTrade
    ```

2. **Create a Virtual Environment (recommend)**
    ```sh
    python -m venv venv
    source venv/bin/activate  
    # On Windows use: venv\Scripts\activate
    ```

3. **Install dependencies**
    ```sh
    pip install -r requirements.txt
    ```

4. **Apply Database Migrations**
    ```sh
    python manage.py makemigrations
    python manage.py migrate
    ```

5. **Run the Development Server**
    ```sh
    python manage.py runserver
    ```

Then, open `http://127.0.0.1:8000` in your browser to view the application.

##### Testing

Project includes a suite of unit tests using Django's `TestCase`. Tests cover login redirections, item logic validation, and concurrency checkouts.

To run test suite:
```sh
python manage.py test
```