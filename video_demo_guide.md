# 🎥 Video Demonstration Guide: Automated Outreach Pipeline

Here is a step-by-step script and recording plan to create a compelling video demonstration of your project for the Vocallabs evaluation. 

## 📝 Preparation Before Recording
1. **Clean up your terminal**: Run `clear` so you have a blank slate.
2. **Open Brevo Dashboard**: Have your Brevo dashboard open in a browser tab on the **Transactional -> Logs** page, ready to show that emails were actually sent.
3. **Open the Project Directory**: Have your VS Code (or preferred IDE) open so you can quickly show the codebase.
4. **Keep it under 3-5 minutes**: Interviewers watch many of these. Be concise, energetic, and clear.

---

## 🎬 Step-by-Step Video Script

### 1. Introduction (0:00 - 0:30)
**Action**: Screen recording of your IDE or a simple slide showing the architecture.
*   **What to say**: "Hi, I'm Naresh Sai Aravind, and this is my Automated Outreach Pipeline for the Vocallabs assignment. The goal was to build a system with zero humans in the loop—one domain in, personalized emails out."
*   **Architecture breakdown**: "My pipeline runs in 4 stages: 
    1. **Ocean.io** for finding lookalike companies. 
    2. **Prospeo** for identifying C-Suite decision-makers. 
    3. **Eazyreach (or Prospeo fallback)** to resolve verified work emails.
    4. **Brevo** to send personalized outreach."

### 2. Addressing the Ocean.io Requirement (0:30 - 0:45)
**Action**: Show the `pipeline/mock_ocean.py` file or the CLI help command.
*   **What to say**: "Because Ocean.io requires a company email on a custom domain to sign up, I built the full Ocean.io integration in the code, but for this live demo, I'll use a `--mock-ocean` flag. This provides curated real-company data for Stage 1, allowing Stages 2, 3, and 4 to run live against real Prospeo and Brevo APIs."

### 3. The Live Demo (0:45 - 2:00)
**Action**: Switch to your terminal and run the pipeline.
*   **What to say**: "Let's run it live. I'll provide a single seed domain, `intercom.com`, and limit it to 3 companies and 1 contact per company for speed."
*   **Command to run during the video**: 
    ```bash
    python outreach.py intercom.com --mock-ocean --max-companies 3 --max-contacts 1
    ```
*   **While it runs**: "The system is now bypassing Ocean.io using our curated mock data. It's currently hitting the live Prospeo API to find decision-makers at Freshworks, Zendesk, and Drift. It handles rate limits automatically with exponential backoff. Now, it's resolving verified emails. We hit the safety checkpoint—here is the summary of the verified contacts."
*   **Action**: Press `y` to proceed past the checkpoint to send the emails. "I'll proceed to trigger the live Brevo API."

### 4. Proving It Works (2:00 - 2:45)
**Action**: Open the `output/` folder and show the generated CSVs. Then switch to your web browser.
*   **What to say**: "The pipeline finished successfully. At every stage, it generated a timestamped CSV report. Here is the final Stage 4 result showing the `message_id` and `sent` status."
*   **Action**: Go to the Brevo Transactional Logs tab and refresh the page.
*   **What to say**: "To prove this works end-to-end, here is my live Brevo dashboard. As you can see, the personalized emails were just successfully delivered to the recipients."

### 5. Code Walkthrough & Edge Cases (2:45 - 3:30)
**Action**: Briefly show `pipeline/stage2_prospeo.py` and `utils/http_client.py`.
*   **What to say**: "A quick look at the codebase: 
    *   **Modularity**: Each stage is an independent module with Pydantic models acting as data contracts between them.
    *   **Resilience**: I built a custom HTTP client that handles 429 Rate Limits and 5xx errors using exponential backoff.
    *   **Data Integrity**: I implemented de-duplication by domain and email to ensure we never spam the same person twice."

### 6. Conclusion (3:30)
*   **What to say**: "That's the pipeline. It's fully automated, resilient to messy data, and production-ready. The code is available on my GitHub. Thank you!"

---

## 💡 Quick Tips for Recording
*   **Software**: You can use tools like **Loom**, **OBS Studio**, or Mac's built-in QuickTime/Windows Game Bar to record your screen and voice. Loom is highly recommended because it immediately gives you a shareable link.
*   **No background noise**: Make sure you are in a quiet room.
*   **Zoom in**: Ensure your terminal text is large enough to be easily readable on a laptop screen.
