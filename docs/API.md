# API Reference

Base URL: `http://localhost:8000`

## Endpoints

### 1. Deploy Lab
Queues a new infrastructure deployment. Returns immediately.

* **POST** `/deploy`
* **Body:**
    ```json
    {
      "scenario_name": "basic_pentest",
      "user_id": "team-01"
    }
    ```
* **Response:** `202 Accepted`

### 2. Check Status
Poll this endpoint to retrieve IPs and credentials once the lab is `active`.

* **GET** `/status/{instance_id}`
* **Response:**
    ```json
    {
      "status": "active",
      "outputs": {
        "attacker_ip": "192.168.1.50",
        "ssh_password": "..."
      }
    }
    ```

### 3. List All Labs
* **GET** `/list`

### 4. Destroy Lab
* **DELETE** `/destroy/{instance_id}`
