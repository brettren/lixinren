
input_data = '"Brett Ren",
            "MOB-38556",
            "LegacyFeedback",
            RuleEnum.Priority.P1,
            RuleEnum.Category.Regression,
            "Instance",
            "1.Verify that user can navigate to feedback home page via feedback tab when enabled with CPM" +
            "2.Verify that user can navigate to feedback home page via CPM when enabled" +
            "3.Verify that feedbacks are shown in Feedback list page if having feedback access permission" +
            "4.Verify that user can access feedback detail page from list page",
            ""'

owner = input_data[0]
testcaseID = input_data[1]
feature = input_data[2]
priority = input_data[3]
category = input_data[4]
instance = input_data[5]
step = input_data[6]
precondition = input_data[7]

output = f"owner = {owner},\n" \
         f"testcaseID = {testcaseID},\n" \
         f"feature = {feature},\n" \
         f"priority = {priority},\n" \
         f"category = {category},\n" \
         f"instance = {instance},\n" \
         f"step = {step},\n" \
         f"precondition = {precondition}"

print(output)