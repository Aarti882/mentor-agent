import threading
import time
import requests
import sys
import uvicorn

# Import the app instance
from main import app

def run_server():
    """Starts the FastAPI server programmatically on port 8001."""
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")

def test_api_server():
    print("=== STARTING BACKEND REST API GATEWAY VERIFICATION TESTS ===")
    
    # Spawn the uvicorn server in a daemon thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for the server to bind to port 8001
    time.sleep(2)
    
    base_url = "http://127.0.0.1:8001/api"
    
    try:
        # 1. Test User Registration
        print("1. Testing Registration Endpoint (/api/auth/register) with OTP...")
        test_email = "test_integration@mca.edu"
        
        # Request OTP
        send_otp_res = requests.post(f"{base_url}/auth/send-otp", json={"email": test_email})
        assert send_otp_res.status_code == 200, "Send OTP failed"
        debug_code = send_otp_res.json()["debug_otp"]
        assert debug_code is not None, "Debug OTP missing in simulation mode"
        
        # Verify OTP
        verify_res = requests.post(f"{base_url}/auth/verify-otp", json={"email": test_email, "code": debug_code})
        assert verify_res.status_code == 200, "Verify OTP failed"
        
        reg_payload = {
            "name": "Integration Test Candidate",
            "email": test_email,
            "password": "securepassword123"
        }
        
        reg_res = requests.post(f"{base_url}/auth/register", json=reg_payload)
        print("Registration response code:", reg_res.status_code)
        
        if reg_res.status_code == 200 or reg_res.status_code == 201:
            reg_data = reg_res.json()
            assert reg_data["user_id"] is not None, "Failed to return user_id on registration"
            print("Registration success! User ID:", reg_data["user_id"])
        elif reg_res.status_code == 400:
            print("Registration returned 400 (User likely already exists). Proceeding to login test...")
        else:
            raise AssertionError(f"Registration failed with code {reg_res.status_code}: {reg_res.text}")

        # 2. Test User Login
        print("2. Testing Login Endpoint (/api/auth/login)...")
        login_payload = {
            "email": "test_integration@mca.edu",
            "password": "securepassword123"
        }
        
        login_res = requests.post(f"{base_url}/auth/login", json=login_payload)
        print("Login response code:", login_res.status_code)
        assert login_res.status_code == 200, f"Login failed with code {login_res.status_code}: {login_res.text}"
        
        login_data = login_res.json()
        user_id = login_data["user_id"]
        assert user_id is not None, "Failed to return user_id on login"
        print(f"Login success! Authenticated User: {login_data['name']}, ID: {user_id}")

        # 3. Test Roadmap Retrieval
        print("3. Testing Roadmap Retrieval Endpoint (/api/users/{user_id}/roadmap)...")
        roadmap_res = requests.get(f"{base_url}/users/{user_id}/roadmap")
        print("Roadmap response code:", roadmap_res.status_code)
        assert roadmap_res.status_code == 200, "Roadmap fetch failed"
        roadmap_data = roadmap_res.json()
        print("Roadmap message:", roadmap_data.get("message", "Data loaded"))

        # 4. Test History Logs
        print("4. Testing History Retrieval Endpoint (/api/users/{user_id}/history)...")
        history_res = requests.get(f"{base_url}/users/{user_id}/history")
        print("History response code:", history_res.status_code)
        assert history_res.status_code == 200, "History fetch failed"

        # 5. Test Direct OAuth Direct Login
        print("5. Testing Direct Simulated OAuth Endpoint (/api/auth/direct) with OTP...")
        direct_email = "test_direct_oauth@mca.edu"
        
        # Request OTP
        send_otp_res2 = requests.post(f"{base_url}/auth/send-otp", json={"email": direct_email})
        assert send_otp_res2.status_code == 200, "Send OTP failed for direct auth"
        debug_code2 = send_otp_res2.json()["debug_otp"]
        assert debug_code2 is not None, "Debug OTP missing for direct auth"
        
        # Verify OTP
        verify_res2 = requests.post(f"{base_url}/auth/verify-otp", json={"email": direct_email, "code": debug_code2})
        assert verify_res2.status_code == 200, "Verify OTP failed for direct auth"
        
        direct_payload = {
            "name": "Direct Test Candidate",
            "email": direct_email
        }
        direct_res = requests.post(f"{base_url}/auth/direct", json=direct_payload)
        print("Direct auth response code:", direct_res.status_code)
        assert direct_res.status_code == 200, "Direct auth endpoint failed"
        direct_data = direct_res.json()
        assert direct_data["user_id"] is not None, "Direct auth did not return user ID"
        print(f"Direct auth success! User ID: {direct_data['user_id']}, Name: {direct_data['name']}")

        # 6. Test User Listing Endpoint
        print("6. Testing User Listing Endpoint (/api/users)...")
        list_res = requests.get(f"{base_url}/users")
        print("User list response code:", list_res.status_code)
        assert list_res.status_code == 200, "User list fetch failed"
        users_list = list_res.json()
        assert len(users_list) > 0, "Returned empty user list"
        print(f"User list fetch success! Found {len(users_list)} registered users.")
        
        print("\n=== ALL BACKEND REST API GATEWAY TESTS PASSED SUCCESSFULLY! ===")
        
    except AssertionError as ae:
        print(f"\n[ERROR] Assertion Error: {ae}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_api_server()
