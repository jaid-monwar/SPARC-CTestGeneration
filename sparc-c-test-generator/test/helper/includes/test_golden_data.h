// Auto-generated from test/data/bst/test_golden_data.json

#ifndef GOLDEN_JSON_DATA_H
#define GOLDEN_JSON_DATA_H

static const char *golden_json_data =
    "{\n  \"insert_single_node\": {\n    \"key\": 50\n  },\n  \"delete_node_leaf\": {\n    \"key\": 50\n  },\n  \"insert_multiple_nodes\": {\n    \"key\": 50,\n    \"left\": {\n      \"key\": 30,\n      \"left\": { \"key\": 20 },\n      \"right\": { \"key\": 40 }\n    },\n    \"right\": {\n      \"key\": 70,\n      \"left\": { \"key\": 60 },\n      \"right\": { \"key\": 80 }\n    }\n  },\n  \"min_value_node_test\": {\n    \"key\": 50,\n    \"left\": {\n      \"key\": 30\n    },\n    \"right\": {\n      \"key\": 70\n    }\n  }\n}\n";

#endif // GOLDEN_JSON_DATA_H
