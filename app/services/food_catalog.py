"""Food labels the AI recognises, grouped into categories with shelf lives.

`shelf_hours` = how long food of this category stays safe at room temperature
after preparation. These are conservative guidance values used to prioritise
pickups, not a substitute for a food-safety inspection.
"""

CATEGORIES = {
    "rice":            {"name": "Rice dishes",            "shelf_hours": 6,  "non_veg": False},
    "curry_dal":       {"name": "Curries & dals",         "shelf_hours": 6,  "non_veg": False},
    "veg_sabzi":       {"name": "Vegetable dishes",       "shelf_hours": 6,  "non_veg": False},
    "meat_egg_fish":   {"name": "Meat, egg & fish",       "shelf_hours": 4,  "non_veg": True},
    "breads":          {"name": "Rotis & breads",         "shelf_hours": 12, "non_veg": False},
    "south_indian":    {"name": "South Indian & snacks",  "shelf_hours": 6,  "non_veg": False},
    "fried_snacks":    {"name": "Fried snacks",           "shelf_hours": 12, "non_veg": False},
    "dairy_sweets":    {"name": "Sweets & dairy",         "shelf_hours": 4,  "non_veg": False},
    "baked":           {"name": "Bakery items",           "shelf_hours": 24, "non_veg": False},
    "fast_food":       {"name": "Fast food",              "shelf_hours": 6,  "non_veg": False},
    "salad":           {"name": "Salads & cut fruit",     "shelf_hours": 4,  "non_veg": False},
    "fruits":          {"name": "Whole fruits",           "shelf_hours": 48, "non_veg": False},
    "raw_vegetables":  {"name": "Raw vegetables",         "shelf_hours": 48, "non_veg": False},
    "packaged":        {"name": "Packaged food",          "shelf_hours": 72, "non_veg": False},
}

# (key, display name, description used in the CLIP prompt, category)
DISHES = [
    ("biryani", "Biryani", "biryani, spiced Indian rice with meat or vegetables", "rice"),
    ("pulao", "Veg pulao", "vegetable pulao rice", "rice"),
    ("plain_rice", "Steamed rice", "plain white steamed rice", "rice"),
    ("fried_rice", "Fried rice", "fried rice", "rice"),
    ("khichdi", "Khichdi", "khichdi, rice and lentil porridge", "rice"),
    ("dal", "Dal", "dal, Indian lentil curry", "curry_dal"),
    ("rajma", "Rajma", "rajma, red kidney bean curry", "curry_dal"),
    ("chole", "Chole", "chole, chickpea curry", "curry_dal"),
    ("sambar", "Sambar", "sambar, South Indian lentil and vegetable stew", "curry_dal"),
    ("paneer_curry", "Paneer curry", "paneer curry with cottage cheese cubes in gravy", "curry_dal"),
    ("kadhi", "Kadhi", "kadhi, yellow yogurt curry", "curry_dal"),
    ("mixed_veg", "Mixed veg sabzi", "mixed vegetable sabzi", "veg_sabzi"),
    ("aloo_sabzi", "Aloo sabzi", "aloo sabzi, Indian potato curry", "veg_sabzi"),
    ("palak", "Palak / saag", "palak saag, green spinach curry", "veg_sabzi"),
    ("chicken_curry", "Chicken curry", "chicken curry", "meat_egg_fish"),
    ("butter_chicken", "Butter chicken", "butter chicken", "meat_egg_fish"),
    ("mutton_curry", "Mutton curry", "mutton curry", "meat_egg_fish"),
    ("egg_curry", "Egg curry", "egg curry with boiled eggs", "meat_egg_fish"),
    ("fish_curry", "Fish curry", "fish curry", "meat_egg_fish"),
    ("roti", "Roti / chapati", "roti chapati, Indian flatbread", "breads"),
    ("naan", "Naan", "naan bread", "breads"),
    ("paratha", "Paratha", "paratha, layered Indian flatbread", "breads"),
    ("puri", "Puri", "puri, deep fried puffed Indian bread", "breads"),
    ("idli", "Idli", "idli, steamed rice cakes", "south_indian"),
    ("dosa", "Dosa", "dosa, thin crispy South Indian crepe", "south_indian"),
    ("poha", "Poha / upma", "poha or upma, Indian breakfast", "south_indian"),
    ("samosa", "Samosa", "samosa", "fried_snacks"),
    ("pakora", "Pakora", "pakora, fried vegetable fritters", "fried_snacks"),
    ("kheer", "Kheer", "kheer, Indian rice pudding", "dairy_sweets"),
    ("gulab_jamun", "Gulab jamun", "gulab jamun", "dairy_sweets"),
    ("rasgulla", "Rasgulla", "rasgulla, white syrupy sweet balls", "dairy_sweets"),
    ("halwa", "Halwa", "halwa, Indian sweet pudding", "dairy_sweets"),
    ("ladoo", "Ladoo / mithai", "ladoo and Indian sweets mithai", "dairy_sweets"),
    ("cake", "Cake / pastry", "cake or pastries", "baked"),
    ("bread", "Bread / buns", "loaf of bread or buns", "baked"),
    ("pizza", "Pizza", "pizza", "fast_food"),
    ("burger", "Burger", "burger", "fast_food"),
    ("sandwich", "Sandwich", "sandwich", "fast_food"),
    ("noodles", "Noodles / chowmein", "chowmein noodles", "fast_food"),
    ("pasta", "Pasta", "pasta", "fast_food"),
    ("salad", "Salad", "fresh salad", "salad"),
    ("fruits", "Fresh fruits", "fresh whole fruits like bananas, apples and oranges", "fruits"),
    ("vegetables", "Raw vegetables", "raw uncooked vegetables", "raw_vegetables"),
    ("packaged", "Packaged food", "packaged food in sealed packets", "packaged"),
]

DISH_TEMPLATES = ["a photo of {}, a type of food.", "a photo of {}."]

# Food / not-food check. Spoiled food still counts as food, so it lands on the food side.
FOOD_PROMPTS = [
    "a photo of food",
    "a photo of a meal or dish",
    "a photo of cooked food in a container",
    "a photo of rotten or moldy food",
    "a photo of fruit or vegetables",
    "a photo of packaged food",
]
NOT_FOOD_PROMPTS = [
    "a photo of a person",
    "a photo of an empty table or room",
    "a screenshot or document",
    "a photo of an object that is not food",
    "a photo of an animal",
    "a photo of a building or street",
]

# Freshness: only FRESH vs SPOILED matter. The distractor classes give CLIP another
# explanation for grease, foil, dim light or charring, which otherwise get mistaken
# for spoilage (fresh samosas on foil scored ~90% "spoiled" without them).
FRESH_PROMPTS = [
    "a photo of fresh food",
    "a photo of freshly cooked food",
    "a photo of food that is good to eat",
]
SPOILED_PROMPTS = [
    "a photo of moldy food",
    "a photo of rotten food",
    "a photo of food covered in fuzzy mold",
]
FRESHNESS_DISTRACTORS = [
    ["a photo of oily, greasy fried food", "a photo of deep fried snacks"],
    ["a photo of food wrapped in aluminium foil or paper", "a photo of takeaway food in packaging"],
    ["a dark, dimly lit photo of food", "a blurry photo of food"],
    ["a photo of grilled, charred or browned food", "a photo of food with melted cheese and toppings"],
]

# (prompt, label, min servings, max servings)
QUANTITY_BUCKETS = [
    ("a photo of a single plate or bowl of food", "1 plate / bowl", 1, 3),
    ("a photo of a few plates or food boxes", "a few plates / boxes", 3, 10),
    ("a photo of a large pot, tray or container of food", "a large pot / tray", 10, 40),
    ("a photo of many large vessels of food for a big event", "many large vessels", 40, 200),
]
