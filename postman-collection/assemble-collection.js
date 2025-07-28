const fs = require('fs');
const path = require('path');

// Read all JSON files in order
const files = [
    '01-collection-info.json',
    '02-authentication.json',
    '03-workspaces.json',
    '04-venues.json',
    '05-users.json',
    '06-tables.json',
    '07-menu.json',
    '08-orders.json',
    '09-public-ordering.json',
    '10-dashboard-analytics.json',
    '11-system-health.json',
    '12-testing-demo.json',
    '13-mobile-support.json',
    '14-notifications.json',
    '15-payments-billing.json',
    '16-reports.json'
];

// Read the collection info (base structure)
const collectionInfo = JSON.parse(fs.readFileSync('01-collection-info.json', 'utf8'));

// Initialize the complete collection
const completeCollection = {
    ...collectionInfo,
    item: []
};

// Add all sections to the collection
for (let i = 1; i < files.length; i++) {
    const sectionData = JSON.parse(fs.readFileSync(files[i], 'utf8'));
    completeCollection.item.push(sectionData);
}

// Write the complete collection
fs.writeFileSync('../Dino_Backend_API_Collection_Complete.postman_collection.json', 
    JSON.stringify(completeCollection, null, 2));

console.log('✅ Complete Postman collection assembled successfully!');
console.log('📁 Output: Dino_Backend_API_Collection_Complete.postman_collection.json');
console.log('📊 Total sections:', completeCollection.item.length);
console.log('🔗 Total endpoints:', countEndpoints(completeCollection.item));

function countEndpoints(items) {
    let count = 0;
    for (const item of items) {
        if (item.request) {
            count++;
        } else if (item.item) {
            count += countEndpoints(item.item);
        }
    }
    return count;
}