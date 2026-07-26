import requests
import time

def run_test():
    # Create a dummy image file
    with open("test_img.jpg", "wb") as f:
        f.write(b"dummy image data")
    
    print("Uploading file...")
    with open("test_img.jpg", 'rb') as f:
        resp = requests.post("http://localhost:8000/api/v1/datasets", files={"file": f})
    ds = resp.json()
    print("Dataset:", ds)
    
    ds_id = ds['id']
    
    print("Starting detection...")
    req = {
      "dataset_id": ds_id,
      "fwhm": 3.0,
      "threshold_sigma": 5.0,
      "motion_threshold": 0.5,
      "min_persistence": 2,
      "enable_motion_detection": True,
      "enable_false_positive_filter": True
    }
    
    resp = requests.post("http://localhost:8000/api/v1/detection/run", json=req)
    task = resp.json()
    print("Task:", task)
    
    task_id = task['id']
    
    print("Polling task...")
    for _ in range(10):
        resp = requests.get(f"http://localhost:8000/api/v1/tasks/{task_id}")
        t = resp.json()
        print("Status:", t['status'], "Message:", t['message'])
        if t['status'] in ['completed', 'failed']:
            break
        time.sleep(1)

if __name__ == "__main__":
    run_test()
