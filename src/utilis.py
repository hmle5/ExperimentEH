from flask import request, session, flash, redirect, url_for
import hashlib
import os
import json
import random
import string
import pandas as pd


# Utilities
def get_client_ip():
    return request.remote_addr


def get_user_agent():
    return request.headers.get("User-Agent")


def generate_unique_participant_id():
    ip = get_client_ip()
    user_agent = get_user_agent()
    unique_string = f"{ip}-{user_agent}"
    return hashlib.sha256(unique_string.encode()).hexdigest()


NEWS_FILE = "news_story.json"

HOLMES_ARTICLE = {
    "title": "Elizabeth Holmes, Theranos C.E.O. and Silicon Valley Star, Accused of Fraud",
    "content": """Holding up a few drops of blood, Elizabeth Holmes became a darling of Silicon Valley by promising that her company’s new device would give everyday Americans unlimited control over their health with a single finger prick.
Ms. Holmes, a Stanford University dropout who founded her company, Theranos, at age 19, captivated investors and the public with her invention: a technology cheaply done at a local drugstore that could detect a range of illnesses, from diabetes to cancer.
With that carefully crafted pitch, Ms. Holmes, whose striking stage presence in a uniform of black turtlenecks drew comparisons to Steve Jobs, became an overnight celebrity, featured on magazine covers and richest-woman lists and in glowing articles.
Her fall — and the near-collapse of Theranos — has been equally dramatic in the last few years. On Wednesday, the Securities and Exchange Commission charged Ms. Holmes, now 34, with widespread fraud, accusing her of exaggerating — even lying — about her technology while raising $700 million from investors.""",
    "source": "The New York Times",
    "question": "What was the product promised by Elizabeth Holmes’ start-up and what happened to it?",
    "options": [
        "The product was a medical device that could cure cancer. However, it was not cleared for approval to be used in hospitals.",
        "The product was an invention that could diagnose diabetes. However, it was not successful in achieving a market scale-up.",
        "The product was a technology that could diagnose illnesses using minimal blood samples. However, it was accused of fraud.",
    ],
    "correct_answer": "The product was a technology that could diagnose illnesses using minimal blood samples. However, it was accused of fraud.",
}

CONTROL_ARTICLE = {
    "title": "Inflation Remains Top Concern, As Revenue Worries Grow",
    "content": """This quarter, the MetLife & U.S. Chamber of Commerce Small Business Index is 62.3, down from last quarter’s Index Score of 69.1, but matching this time last year (62.3). While most Index measures are not down significantly this quarter, there is a slight softening across measures of business health, cash flow, and increases in staff.
However, according to the results of the survey (conducted between January 28 – February 14), views of the U.S. and local economies are stable this quarter. Around three in ten small businesses (29%) believe that the U.S. economy is in good health and 37% say the same of their local economy. Both of these measures are on par with last quarter and Q1 2024.
The survey’s findings also show that inflation continues to be small business owners’ top concern by far and this concern is at record highs—although concerns about revenue also jumped this month. In fact, consistent for the past three years, inflation (58%) continues to be the biggest challenge facing small businesses.
""",
    "source": "U.S. Chamber of Commerce",
    "question": "Based on the news report, which statement best summarizes small businesses' current views about the U.S. economy?",
    "options": [
        "Although inflation remains a record-high concern for businesses, reduction in revenue has recently been their biggest worry.",
        "Despite some decreases in business performance measures, small businesses remain broadly optimistic about easing inflation.",
        "About one-third of small businesses believe the economy is in good health, but inflation continues to be their biggest challenge.",
    ],
    "correct_answer": "About one-third of small businesses believe the economy is in good health, but inflation continues to be their biggest challenge.",
}

CONTROL_FRAUD_ARTICLE = {
    "title": "Keep it Real: The SEC Renews Warning About ‘Startup Culture’",
    "content": """Last week, The Wall Street Journal published an article titled: “SEC Sends a Message to Startups About ‘Fake It’ Culture.” According to the article, the “startup culture” at issue “encouraged setting lofty or even unrealistic growth projections to maximize company potential and catch the attention of investors and customers.”
Culturally, some might view “fake it until you make it” as a simple testament to the faith and hope that business founders have in their company’s innovations and inventions. The U.S. Securities and Exchange Commission’s recent enforcement actions serve as a reminder that startup fundraisers cannot use the “fake it until you make it” ethos to whitewash lying to investors. 
Why did the SEC choose to issue this reminder now? The agency did not say. But with the stock markets at record highs, and the promises of billions of dollars to be made in artificial intelligence investments discussed at every turn, excessive frothiness on Wall Street can easily lead to overeager investors in startup land whose investment decisions are governed more by FOMO (the “fear of missing out”) than sound financial analysis. 
""",
    "source": "The National Law Review and U.S. Chamber of Commerce",
    "question": "What was the reminder issued by the U.S. Securities and Exchange Commission (SEC), and why did the agency do it?",
    "options": [
        "The SEC emphasized the value of the start-up culture in unlocking company potential, amid the positive outlook for high-tech investments.",
        "The SEC warned that unrealistic growth projections by start-ups misled investors and customers, thus worsening the current stock market.",
        "The SEC reminded founders and investors that the startup culture often exaggerates a company's true potential, amid overenthusiasm around AI.",
    ],
    "correct_answer": "The SEC reminded founders and investors that the startup culture often exaggerates a company's true potential, amid overenthusiasm around AI.",
}

BANKMAN_ARTICLE = {
    "title": "S.E.C. Charges Sam Bankman-Fried With Defrauding FTX Investors",
    "content": """U.S. regulators filed civil securities fraud charges on Tuesday against Sam Bankman-Fried, the founder of the collapsed FTX crypto exchange, who was arrested on Monday night at his home in the Bahamas. The Securities and Exchange Commission charged him with misleading big investors, who committed nearly $2 billion to FTX in recent years, about the financial health of the crypto exchange and its partner crypto trading platform, Alameda Research.
The S.E.C. also said that Mr. Bankman-Fried misled customers by taking in billions of dollars to trade crypto on FTX and telling them it was safe. But the S.E.C. said that money from customers was commingled with funds at Alameda and used to finance investments in outside ventures, buy real estate and make political donations.
The collapse of the FTX empire shocked the crypto world and has caused many investors to get to grips with not just the volatility of crypto assets but the security and safety of the platforms that crypto is traded on. FTX was one of the biggest exchanges in the world and spent extensively on advertising and marketing.
""",
    "source": "The New York Times",
    "question": "What was the product offered by Sam Bankman-Fried’s start-up and what happened to it?",
    "options": [
        "FTX was one of the largest cryptocurrency trading platforms. However, its founder was charged with embezzling funds from a partner crypto platform.",
        "FTX was one of the biggest crypto exchange platforms. However, its founder was accused of disclosing customers’ real estate investments and political donations.",
        "FTX was one of the most prominent crypto exchange platforms. However, its founder was charged with defrauding investors and misusing customers’ funds.",
    ],
    "correct_answer": "FTX was one of the most prominent crypto exchange platforms. However, its founder was charged with defrauding investors and misusing customers’ funds.",
}


def generate_news_story_file():
    """Create the JSON file at startup if it does not exist."""
    if os.path.exists(NEWS_FILE):
        return  # File already exists, do nothing

    def generate_code():
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # Generate 500 unique entries for each story type
    # Pilot 1: 90 unique entries for each story type
    # Pilot 2: 80 unique entries for each story type
    # Pilot 2: Replace control_article with bankman
    stories = []
    for _ in range(90):
        stories.append({"code": generate_code(), "used": False, "story": "holmes"})
        #stories.append({"code": generate_code(), "used": False, "story": "control_news"})
        stories.append({"code": generate_code(), "used": False, "story": "control_fraud_news"})
        stories.append({"code": generate_code(), "used": False, "story": "bankman"})

    # Save to JSON file
    with open(NEWS_FILE, "w") as f:
        json.dump(stories, f, indent=4)


def get_unused_story():
    """Fetch a random unused story entry but DO NOT mark it as used yet."""
    if not os.path.exists(NEWS_FILE):
        generate_news_story_file()  # Ensure the file exists

    with open(NEWS_FILE, "r") as f:
        stories = json.load(f)

    # Find all unused stories
    unused_stories = [story for story in stories if not story["used"]]

    if not unused_stories:
        return None  # No unused stories left

    # Randomly select one
    selected_story = random.choice(unused_stories)

    return selected_story  # Return but don't mark as used yet


def mark_story_as_used(story_code):
    """Mark the story as used only if the user answers correctly."""
    if not os.path.exists(NEWS_FILE):
        return  # No file means no data to update

    with open(NEWS_FILE, "r") as f:
        stories = json.load(f)

    for story in stories:
        if story["code"] == story_code:
            story["used"] = True  # Now mark it as used

    # Save updated JSON file
    with open(NEWS_FILE, "w") as f:
        json.dump(stories, f, indent=4)


# === CONFIGURABLE CONSTANTS ===
DEFAULT_EXCEL_PATH = "data/clean_data_new.xlsx"
DEFAULT_JSON_PATH = "startup_data.json"
DEFAULT_NUM_SETS = 300
DEFAULT_SET_SIZE = 4
DEFAULT_CODE_LENGTH = 10


def normalize_text(text):
    """Fix unicode artifacts like curly quotes, non-breaking spaces, etc."""
    if pd.isna(text):
        return ""
    return (
        str(text)
        .replace("\xa0", " ")  # non-breaking space
        .replace("\u2019", "'")  # curly apostrophe
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .strip()
    )


def load_excel_data(excel_path):
    """Load and normalize all string fields in both sheets."""
    sheets = pd.read_excel(excel_path, sheet_name=None)
    startup_df = sheets["startup"]
    founder_df = sheets["founder"]
    value_df = sheets["value"]

    # Normalize string fields in both DataFrames
    for df in (startup_df, founder_df, value_df):
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].apply(normalize_text)

    return startup_df, founder_df, value_df


def generate_unique_code(existing_codes, length=8):
    """Generate a unique alphanumeric code not already in use."""
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if code not in existing_codes:
            return code


def prepare_randomized_startup_set(
    #startup_df, founder_firstname, evaluation_sentences, set_size
    startup_df, founder_firstname_male, founder_firstname_female, evaluation_sentences, set_size
):
    """Prepare one startup set with normalized data and substituted evaluation sentence."""
    selected_startups = startup_df.sample(n=set_size, replace=False).to_dict(
        orient="records"
    )
    #assigned_founders = random.sample(founder_firstname, set_size)
    # now randomly select 3 male names and 1 female name from list and randomize order
    male_names = [(name, "male") for name in random.sample(founder_firstname_male, 3)]
    female_names = [(name, "female") for name in random.sample(founder_firstname_female, 1)]
    assigned_founders = male_names + female_names
    random.shuffle(assigned_founders)
    # now for set of size 4 we have 3 external and 2 self-eva list
    assigned_sentences = random.sample(evaluation_sentences, set_size)

    combined = []
    for i, startup in enumerate(selected_startups):
        #founder_fullname = f"{assigned_founders[i]} {startup['Founder_lastname_altered']}"
        first_name, gender = assigned_founders[i]
        founder_fullname = f"{first_name} {startup['Founder_lastname_altered']}"
        sentence = f"{assigned_sentences[i]} {startup['Valuation_amount']}."

        combined.append(
            {
                "Startup_name": startup["Startup_name_altered"],
                "Industry": startup["Industry"],
                "Product_info": startup["Product_info_altered"],
                "Founded": (
                    int(startup["Founded_10"])
                    if not pd.isna(startup["Founded_10"])
                    else None
                ),
                "Founder_age": (
                    int(startup["Founder_inferred_age"])
                    if not pd.isna(startup["Founder_inferred_age"])
                    else None
                ),
                "Founder_Nstartups": startup["Founder_Nstartups"],
                "Assigned_Founder": founder_fullname,
                "Founder_gender": gender,
                "Evaluation_sentence": sentence,
            }
        )

    random.shuffle(combined)

    # Add order variable: "Startup A", "Startup B", ...
    order_labels = [f"Start-up {chr(65 + i)}" for i in range(set_size)]
    for i, startup in enumerate(combined):
        startup["Order"] = order_labels[i]
    
    return combined


def save_startup_sets_to_json(sets, path):
    """Save the full list of generated sets to a JSON file."""
    with open(path, "w") as f:
        json.dump(sets, f, indent=4)


def generate_startup_sets(
    excel_path=DEFAULT_EXCEL_PATH,
    output_path=DEFAULT_JSON_PATH,
    num_sets=DEFAULT_NUM_SETS,
    set_size=DEFAULT_SET_SIZE,
    code_length=DEFAULT_CODE_LENGTH,
):
    """Generate randomized startup sets and write to JSON if not already existing."""
    if os.path.exists(output_path):
        return False

    startup_df, founder_df, value_df = load_excel_data(excel_path)

    # Ensure required fields are present
    startup_df = startup_df.dropna(
        subset=["Startup_name_altered", "Industry", "Product_info_altered"]
    )
    #founder_firstname = founder_df["Founder_firstname_altered"].dropna().unique().tolist()
    # now first names from male names and female names to ensure we always have 3 males and one female
    founder_firstname_male = founder_df[founder_df["gender"] == "male"]["Founder_firstname_altered"].dropna().unique().tolist()
    founder_firstname_female = founder_df[founder_df["gender"] == "female"]["Founder_firstname_altered"].dropna().unique().tolist()
    evaluation_sentences = value_df["Evaluation_sentence"].dropna().tolist()

    # Validation
    #if len(founder_firstname) < set_size:
    #    raise ValueError("Not enough founder names in Excel to build a full set.")
    if len(founder_firstname_male) < 3 or len(founder_firstname_female) < 1:
         raise ValueError("Not enough male or female founder names to build each set.")


    startup_sets = []
    used_codes = set()

    for _ in range(num_sets):
        startup_data = prepare_randomized_startup_set(
            #startup_df, founder_firstname, evaluation_sentences, set_size
            startup_df, founder_firstname_male, founder_firstname_female, evaluation_sentences, set_size
        )
        code = generate_unique_code(used_codes, length=code_length)
        used_codes.add(code)

        startup_sets.append(
            {
                "code": code,
                "used": False,
                "startups": startup_data,
            }
        )
    
    # === VALIDATION: Check female founder count per set ===
    for s in startup_sets:
        num_females = sum(1 for entry in s["startups"] if entry["Founder_gender"] == "female")
        if num_females != 1:
            print(f"Warning: Set {s['code']} has {num_females} female founders")

    save_startup_sets_to_json(startup_sets, output_path)
    return True


def mark_startup_set_as_used(code, path=DEFAULT_JSON_PATH):
    """
    Mark a startup set as 'used': True in the JSON file for a given code.

    Args:
        code (str): The 10-character startup set code.
        path (str): Path to the JSON file.

    Returns:
        bool: True if update was successful, False if code not found or file missing.
    """
    if not os.path.exists(path):
        return False

    with open(path, "r") as f:
        sets = json.load(f)

    updated = False
    for s in sets:
        if s["code"] == code:
            s["used"] = True
            updated = True
            break

    if updated:
        with open(path, "w") as f:
            json.dump(sets, f, indent=4)
    return updated
