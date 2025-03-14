# *University Bot Portal*  

The *University Bot Portal* is an AI-powered chatbot designed to automate common academic and administrative tasks for students, faculty, and university staff. It provides real-time access to examination schedules, certificate generation, and leave request management through a *custom-built API* and *MongoDB database*, ensuring a seamless university experience.  

## *Features & Functionality*  

### 📅 *Examination Schedule Retrieval*  
- Users can enter a *subject code* (e.g., CS101), and the bot instantly provides the *exam date, time, and venue*.  
- The system queries the *MongoDB database* via a *custom API* to retrieve the latest schedule.  

### 📜 *Certificate Generation*  
- Typing *"certificate"* prompts the bot to offer two options:  
  - *NOC (No Objection Certificate)*  
  - *Bonafide Certificate*  
- Once the user selects the certificate type, the system generates a *downloadable PDF* using stored data from *MongoDB*.  
- Eliminates manual paperwork and speeds up certificate requests.  

### 📝 *Leave Request Management*  
- Both *students and faculty* can apply for *leave* through the portal.  
- Users enter details such as *leave type, dates, and reason*, and the system processes the request.  
- Leave requests are stored in *MongoDB, and responses are handled via the **custom API*.  
- The bot provides a *confirmation status* on whether the leave is *approved or rejected* based on university policies.  

## *Future Updates 🚀*  
🔹 *Live Attendance Portal Integration*  
- The system will be connected to the *university’s attendance portal*.  
- If a student’s *attendance is above 80%, their leave request will be **automatically approved*.  
- Faculty will be notified about leave approvals in real-time.  

## *Technology Stack*  
- *Backend:* Flask (Python) with a *custom API*  
- *Frontend:* HTML, CSS, JavaScript  
- *Database:* *MongoDB*  
- *PDF Generation:* ReportLab/pdfkit  
- *APIs:* RESTful APIs for data retrieval and processing  
- *Deployment:* Docker, AWS  

## *Why Use This Portal?*  
✔ *Custom API* ensures flexibility and scalability.  
✔ *MongoDB database* provides efficient and scalable data storage.  
✔ *Automates routine tasks* to save time for students and faculty.  
✔ *Reduces paperwork* with digital document generation.  
✔ *Improves accessibility* by allowing users to make requests remotely.  

The *University Bot Portal* is a step towards *smart university automation*, making academic and administrative tasks easier and more efficient. 🌟  

---  

This description now highlights your *custom API* and *MongoDB database*. Let me know if you need any more changes! 🚀😃
