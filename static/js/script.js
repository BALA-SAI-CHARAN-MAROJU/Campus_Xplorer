// Update the dropdown options for start and end locations
const predefinedLocations = {
    "Academic Block": [13.263018, 80.027427],
    "Library": [13.262621, 80.026525],
    "Canteen": [13.262856, 80.028401],
    "Pond": [13.262198, 80.027673],
    "AVV Gym for Girls": [13.262141, 80.026830],
    "Chennai": [13.080917019874969, 80.26358605588356],
    "Delhi": [28.675015901626473, 77.21675859763418],
    "Mumbai": [19.07598369140625, 72.877685546875],
    "Kolkata": [22.5726455078125, 88.3638671875],
    "Hyderabad": [17.432607421875, 78.4736328125],
    "Bengaluru": [12.971593933105469, 77.5945263671875],
    "Junior Girls Hostel": [13.261993, 80.026421],
    "Junior Boys Hostel": [13.261805, 80.028076],
    "Lab Block": [13.262768, 80.028147],
    "Mechanical Lab": [13.261205, 80.027488],
    "Volley Ball Court": [13.261009, 80.027530],
    "Basket Ball Court": [13.260909, 80.027256],
    "Senior Girls Hostel": [13.260658, 80.028184],
    "Senior Boys Hostel": [13.260550, 80.027272],
    "2nd Year Boys Hostel": [13.259570, 80.026694],
    "Amrita Indoor Stadium": [13.259880, 80.025990],
    "AVV Gym for Boys": [13.260146, 80.026143],
    "AVV Ground": [13.259708, 80.025416],
    // Additional campuses / colleges
    "Amrita Coimbatore Campus": [11.0168, 76.9558],
    "Amrita Bengaluru Campus": [12.9663, 77.6069],
    "Amrita Amritapuri Campus": [9.0884, 76.4890]
};

const startLocationSelect = document.getElementById('start-location');
const endLocationSelect = document.getElementById('end-location');

Object.keys(predefinedLocations).forEach(location => {
    const option1 = document.createElement('option');
    option1.value = location;
    option1.textContent = location;
    startLocationSelect.appendChild(option1);

    const option2 = document.createElement('option');
    option2.value = location;
    option2.textContent = location;
    endLocationSelect.appendChild(option2);
}); 