import json
import os

def generate_seed_data():
    videos = [
        {
            "title": "Python for Beginners: Variables & Data Types",
            "description": "Learn the basics of Python variables, integers, strings, floats, and booleans.",
            "module": "Python Programming",
            "topic": "Python Basics",
            "difficulty": "beginner",
            "duration_seconds": 900,
            "video_url": "https://www.youtube.com/embed/k9TUPpGqYTo",
            "thumbnail_url": "https://img.youtube.com/vi/k9TUPpGqYTo/hqdefault.jpg",
            "source_name": "CrashCourse",
            "license_type": "Creative Commons Attribution (CC BY)",
            "attribution": "CrashCourse - Computer Science",
            "source_url": "https://www.youtube.com/watch?v=k9TUPpGqYTo",
            "allow_embedding": True,
            "tags": "Python, Variables, Basics",
            "facts": [
                "A variable in Python is created the moment you first assign a value to it.",
                "Python has no command for declaring a variable.",
                "Variables can change type after they have been set.",
                "You can get the data type of a variable with the type() function.",
                "String variables can be declared either by using single or double quotes.",
                "Variable names are case-sensitive.",
                "A variable name must start with a letter or the underscore character.",
                "A variable name cannot start with a number.",
                "Variable names can only contain alpha-numeric characters and underscores.",
                "Python allows you to assign values to multiple variables in one line.",
                "The print() function is often used to output variables.",
                "To combine both text and a variable, Python uses the + character.",
                "For numbers, the + character works as a mathematical operator.",
                "If you try to combine a string and a number, Python will give you an error.",
                "Global variables are variables that are created outside of a function.",
                "To create a global variable inside a function, you can use the global keyword.",
                "Integers are whole numbers, positive or negative, without decimals.",
                "Floats are numbers, positive or negative, containing one or more decimals.",
                "Complex numbers are written with a 'j' as the imaginary part.",
                "You can convert from one type to another with the int(), float(), and complex() methods.",
                "Booleans represent one of two values: True or False.",
                "The bool() function allows you to evaluate any value, and give you True or False in return.",
                "Almost any value is evaluated to True if it has some sort of content.",
                "Empty strings, 0, and None evaluate to False.",
                "Python does not have a built-in character data type.",
                "A string is essentially an array of characters.",
                "You can access elements of a string using square brackets.",
                "You can loop through the characters in a string using a for loop.",
                "The len() function returns the length of a string.",
                "You can check if a certain phrase or character is present in a string with 'in'."
            ]
        },
        {
            "title": "Introduction to Databases & SQL",
            "description": "Understand relational databases, tables, and basic SQL SELECT queries.",
            "module": "Database Systems",
            "topic": "SQL Basics",
            "difficulty": "beginner",
            "duration_seconds": 1100,
            "video_url": "https://www.youtube.com/embed/HXV3zeQKqGY",
            "thumbnail_url": "https://img.youtube.com/vi/HXV3zeQKqGY/hqdefault.jpg",
            "source_name": "freeCodeCamp.org",
            "license_type": "Creative Commons Attribution (CC BY)",
            "attribution": "freeCodeCamp.org SQL Tutorial",
            "source_url": "https://www.youtube.com/watch?v=HXV3zeQKqGY",
            "allow_embedding": True,
            "tags": "SQL, Databases, Relational",
            "facts": [
                "SQL stands for Structured Query Language.",
                "SQL is used to communicate with a database.",
                "RDBMS stands for Relational Database Management System.",
                "Data in an RDBMS is stored in database objects called tables.",
                "A table is a collection of related data entries and it consists of columns and rows.",
                "A column is a vertical entity in a table that contains all information associated with a specific field.",
                "A row is a single, implicitly structured data item in a table.",
                "The SELECT statement is used to select data from a database.",
                "The data returned is stored in a result table, called the result-set.",
                "SELECT * selects all columns from a table.",
                "The SELECT DISTINCT statement is used to return only distinct (different) values.",
                "The WHERE clause is used to filter records.",
                "The WHERE clause is used to extract only those records that fulfill a specified condition.",
                "The AND, OR and NOT operators are used with the WHERE clause.",
                "The ORDER BY keyword is used to sort the result-set in ascending or descending order.",
                "ORDER BY sorts the records in ascending order by default.",
                "To sort the records in descending order, use the DESC keyword.",
                "The INSERT INTO statement is used to insert new records in a table.",
                "The IS NULL operator is used to test for empty values (NULL values).",
                "The UPDATE statement is used to modify the existing records in a table.",
                "Be careful when updating records. If you omit the WHERE clause, all records will be updated!",
                "The DELETE statement is used to delete existing records in a table.",
                "The TOP clause is used to specify the number of records to return.",
                "The MIN() function returns the smallest value of the selected column.",
                "The MAX() function returns the largest value of the selected column.",
                "The COUNT() function returns the number of rows that matches a specified criterion.",
                "The AVG() function returns the average value of a numeric column.",
                "The SUM() function returns the total sum of a numeric column.",
                "The LIKE operator is used in a WHERE clause to search for a specified pattern in a column.",
                "The IN operator allows you to specify multiple values in a WHERE clause."
            ]
        },
        {
            "title": "Data Structures: Arrays and Linked Lists",
            "description": "Compare arrays and linked lists in terms of memory, insertion, and access time.",
            "module": "Computer Science",
            "topic": "Data Structures",
            "difficulty": "intermediate",
            "duration_seconds": 1200,
            "video_url": "https://www.youtube.com/embed/RBSGKlAvoiM",
            "thumbnail_url": "https://img.youtube.com/vi/RBSGKlAvoiM/hqdefault.jpg",
            "source_name": "HackerRank",
            "license_type": "Creative Commons Attribution (CC BY)",
            "attribution": "HackerRank Data Structures Series",
            "source_url": "https://www.youtube.com/watch?v=RBSGKlAvoiM",
            "allow_embedding": True,
            "tags": "Data Structures, Arrays, Linked Lists",
            "facts": [
                "An array is a collection of items stored at contiguous memory locations.",
                "The elements can be accessed randomly using indices of an array.",
                "The size of an array must be provided before storing data.",
                "In an array, insertion and deletion take O(n) time.",
                "Array elements are stored in contiguous memory.",
                "Accessing an element in an array by index takes O(1) time.",
                "A linked list is a linear data structure, in which the elements are not stored at contiguous memory locations.",
                "The elements in a linked list are linked using pointers.",
                "In a linked list, each element is called a node.",
                "Each node consists of two parts: data and a pointer to the next node.",
                "The size of a linked list is dynamic.",
                "Insertion and deletion operations are easier in a linked list compared to an array.",
                "Accessing an element in a linked list takes O(n) time.",
                "You cannot randomly access elements in a linked list.",
                "Memory is allocated at compile time in arrays.",
                "Memory is allocated at run time in linked lists.",
                "Arrays have better cache locality.",
                "Linked lists consume more memory due to pointers.",
                "In a singly linked list, each node points to the next node.",
                "In a doubly linked list, each node points to both the previous and next nodes.",
                "In a circular linked list, the last node points to the first node.",
                "Deleting the first element of an array takes O(n) time.",
                "Deleting the first node of a linked list takes O(1) time.",
                "Appending an element to a dynamic array takes amortized O(1) time.",
                "Appending an element to a linked list with a tail pointer takes O(1) time.",
                "Searching for an element in an unsorted array takes O(n) time.",
                "Searching for an element in an unsorted linked list takes O(n) time.",
                "Binary search can be efficiently performed on a sorted array.",
                "Binary search cannot be efficiently performed on a linked list.",
                "Arrays are cache-friendly because of contiguous memory."
            ]
        },
        {
            "title": "What is Object-Oriented Programming?",
            "description": "An introduction to classes, objects, inheritance, and polymorphism.",
            "module": "Software Engineering",
            "topic": "OOP",
            "difficulty": "beginner",
            "duration_seconds": 1050,
            "video_url": "https://www.youtube.com/embed/pTB0EiLXUC8",
            "thumbnail_url": "https://img.youtube.com/vi/pTB0EiLXUC8/hqdefault.jpg",
            "source_name": "Programming with Mosh",
            "license_type": "External Embed — License Requires Verification",
            "attribution": "Programming with Mosh - OOP in Python",
            "source_url": "https://www.youtube.com/watch?v=pTB0EiLXUC8",
            "allow_embedding": True,
            "tags": "OOP, Python, Classes",
            "facts": [
                "Object-oriented programming (OOP) is a programming paradigm based on the concept of 'objects'.",
                "An object can contain data, in the form of fields (often known as attributes or properties).",
                "An object can contain code, in the form of procedures (often known as methods).",
                "A class is a blueprint for creating objects.",
                "An object is an instance of a class.",
                "The four main principles of OOP are Encapsulation, Abstraction, Inheritance, and Polymorphism.",
                "Encapsulation is the bundling of data and methods that operate on that data.",
                "Encapsulation restricts direct access to some of an object's components.",
                "Abstraction refers to hiding complex implementation details and showing only the essential features of the object.",
                "Inheritance is a mechanism wherein a new class is derived from an existing class.",
                "The existing class is called the base class, parent class, or superclass.",
                "The new class is called the derived class, child class, or subclass.",
                "Inheritance promotes code reusability.",
                "Polymorphism allows objects of different classes to be treated as objects of a common superclass.",
                "Method overriding is a feature of polymorphism where a subclass provides a specific implementation of a method that is already provided by its superclass.",
                "Method overloading (in some languages) allows a class to have more than one method with the same name, if their argument lists are different.",
                "A constructor is a special method used to initialize objects.",
                "In Python, the __init__() method is used as a constructor.",
                "The 'self' parameter is a reference to the current instance of the class.",
                "Attributes define the state of an object.",
                "Methods define the behavior of an object.",
                "A static method belongs to the class rather than the instance of a class.",
                "A class variable is shared by all instances of a class.",
                "An instance variable is unique to each instance.",
                "An interface defines a contract that classes can implement.",
                "An abstract class cannot be instantiated.",
                "Composition is a design principle where a class contains objects of other classes.",
                "Composition represents a 'has-a' relationship.",
                "Inheritance represents an 'is-a' relationship.",
                "OOP makes code more modular, flexible, and easier to maintain."
            ]
        },
        {
            "title": "Understanding API Design & RESTful Services",
            "description": "Learn the principles of REST, HTTP methods, status codes, and API design.",
            "module": "Web Development",
            "topic": "APIs",
            "difficulty": "intermediate",
            "duration_seconds": 1300,
            "video_url": "https://www.youtube.com/embed/lsMQRaeKNDk",
            "thumbnail_url": "https://img.youtube.com/vi/lsMQRaeKNDk/hqdefault.jpg",
            "source_name": "Academind",
            "license_type": "Creative Commons Attribution (CC BY)",
            "attribution": "Academind REST API concepts",
            "source_url": "https://www.youtube.com/watch?v=lsMQRaeKNDk",
            "allow_embedding": True,
            "tags": "API, REST, Web Development",
            "facts": [
                "API stands for Application Programming Interface.",
                "REST stands for Representational State Transfer.",
                "A REST API uses HTTP requests to access and use data.",
                "REST APIs are stateless, meaning each request from client to server must contain all of the information necessary to understand the request.",
                "GET requests are used to retrieve resource representation/information.",
                "POST requests are used to create new resources.",
                "PUT requests are used to update existing resources entirely.",
                "PATCH requests are used to update existing resources partially.",
                "DELETE requests are used to delete resources.",
                "HTTP status codes are standard response codes given by web servers.",
                "1xx status codes represent informational responses.",
                "2xx status codes represent successful responses.",
                "3xx status codes represent redirects.",
                "4xx status codes represent client errors.",
                "5xx status codes represent server errors.",
                "A 200 OK status code means the request was successful.",
                "A 201 Created status code means a resource was successfully created.",
                "A 400 Bad Request status code means the server could not understand the request due to invalid syntax.",
                "A 401 Unauthorized status code means the client must authenticate itself.",
                "A 403 Forbidden status code means the client does not have access rights to the content.",
                "A 404 Not Found status code means the server can not find the requested resource.",
                "A 500 Internal Server Error means the server has encountered a situation it doesn't know how to handle.",
                "REST APIs communicate primarily via JSON or XML.",
                "JSON stands for JavaScript Object Notation.",
                "Endpoints are URLs where APIs can be accessed.",
                "A URI (Uniform Resource Identifier) identifies a resource.",
                "REST relies on a client-server architecture.",
                "REST systems can be layered, with intermediaries (like proxies or load balancers) between client and server.",
                "Cacheability is a constraint of REST, where responses must define themselves as cacheable or not.",
                "HATEOAS (Hypermedia as the Engine of Application State) is a constraint of REST."
            ]
        },
        {
            "title": "Introduction to React: Components and Props",
            "description": "Discover how to build reusable UI components and pass data using props in React.",
            "module": "Web Development",
            "topic": "Frontend Frameworks",
            "difficulty": "intermediate",
            "duration_seconds": 1400,
            "video_url": "https://www.youtube.com/embed/Ke90Tje7VS0",
            "thumbnail_url": "https://img.youtube.com/vi/Ke90Tje7VS0/hqdefault.jpg",
            "source_name": "Programming with Mosh",
            "license_type": "External Embed — License Requires Verification",
            "attribution": "Programming with Mosh React Tutorial",
            "source_url": "https://www.youtube.com/watch?v=Ke90Tje7VS0",
            "allow_embedding": True,
            "tags": "React, JavaScript, Frontend",
            "facts": [
                "React is a JavaScript library for building user interfaces.",
                "React was created and is maintained by Facebook.",
                "React allows developers to create large web applications that can change data, without reloading the page.",
                "React applications are built out of isolated pieces of code called components.",
                "Components let you split the UI into independent, reusable pieces.",
                "There are two main types of components: functional components and class components.",
                "Functional components are just JavaScript functions that return React elements.",
                "Class components are ES6 classes that extend React.Component.",
                "React uses JSX, a syntax extension to JavaScript.",
                "JSX produces React 'elements'.",
                "Babel compiles JSX down to React.createElement() calls.",
                "You can embed JavaScript expressions in JSX by wrapping them in curly braces {}.",
                "Props are short for properties.",
                "Props are how components talk to each other.",
                "Props are passed to components via HTML attributes.",
                "Props are read-only; a component must never modify its own props.",
                "State allows React components to change their output over time in response to user actions.",
                "State is private and fully controlled by the component.",
                "In functional components, state is managed using the useState hook.",
                "The useState hook returns an array with two elements: the current state value and a function to update it.",
                "When state changes, React re-renders the component.",
                "React uses a Virtual DOM to improve performance.",
                "The Virtual DOM is a lightweight copy of the actual DOM.",
                "React compares the Virtual DOM to the previous Virtual DOM to determine what changed (diffing).",
                "React then only updates the actual DOM where necessary.",
                "A component's lifecycle has three main phases: Mounting, Updating, and Unmounting.",
                "The useEffect hook lets you perform side effects in functional components.",
                "Keys help React identify which items have changed, are added, or are removed in lists.",
                "Keys should be unique among siblings.",
                "React fragments let you group a list of children without adding extra nodes to the DOM."
            ]
        },
        {
            "title": "Machine Learning: Linear Regression Explained",
            "description": "Understand the math behind linear regression, loss functions, and gradient descent.",
            "module": "Machine Learning",
            "topic": "Supervised Learning",
            "difficulty": "intermediate",
            "duration_seconds": 1600,
            "video_url": "https://www.youtube.com/embed/zPG4NjIkCjc",
            "thumbnail_url": "https://img.youtube.com/vi/zPG4NjIkCjc/hqdefault.jpg",
            "source_name": "StatQuest with Josh Starmer",
            "license_type": "External Embed — License Requires Verification",
            "attribution": "StatQuest - Linear Regression",
            "source_url": "https://www.youtube.com/watch?v=zPG4NjIkCjc",
            "allow_embedding": True,
            "tags": "Machine Learning, Regression, Math",
            "facts": [
                "Linear regression is a supervised learning algorithm.",
                "It is used for predicting a continuous numeric value.",
                "The equation of a simple linear regression line is y = mx + c.",
                "In machine learning notation, it is often written as h(x) = theta0 + theta1*x.",
                "The variables theta0 and theta1 are called parameters or weights.",
                "The cost function measures how well the model predicts the target values.",
                "A common cost function for linear regression is Mean Squared Error (MSE).",
                "MSE calculates the average of the squared differences between predicted and actual values.",
                "Gradient descent is an optimization algorithm used to minimize the cost function.",
                "Gradient descent iteratively adjusts the parameters to reduce the cost.",
                "The learning rate determines the size of the steps taken during gradient descent.",
                "If the learning rate is too large, gradient descent can diverge.",
                "If the learning rate is too small, gradient descent will be slow.",
                "Multiple linear regression involves predicting a value based on multiple input features.",
                "Feature scaling can speed up gradient descent.",
                "Normalization and standardization are common feature scaling techniques.",
                "The Normal Equation is an analytical method to find the optimal parameters directly.",
                "The Normal Equation can be slow if the number of features is very large.",
                "Overfitting occurs when a model learns the training data too well, including noise.",
                "Underfitting occurs when a model is too simple to capture the underlying pattern.",
                "Regularization is a technique used to prevent overfitting.",
                "Lasso regression uses L1 regularization.",
                "Ridge regression uses L2 regularization.",
                "L1 regularization can shrink some weights to zero, effectively performing feature selection.",
                "R-squared is a statistical measure of how close the data are to the fitted regression line.",
                "R-squared values range from 0 to 1.",
                "A higher R-squared indicates a better fit.",
                "Residuals are the differences between observed values and predicted values.",
                "In linear regression, the relationship between features and target is assumed to be linear.",
                "Polynomial regression can model non-linear relationships using polynomial features."
            ]
        },
        {
            "title": "Introduction to Docker and Containers",
            "description": "Learn what containers are, how they differ from VMs, and basic Docker commands.",
            "module": "DevOps",
            "topic": "Containerization",
            "difficulty": "intermediate",
            "duration_seconds": 1250,
            "video_url": "https://www.youtube.com/embed/Gjnup-PuquQ",
            "thumbnail_url": "https://img.youtube.com/vi/Gjnup-PuquQ/hqdefault.jpg",
            "source_name": "NetworkChuck",
            "license_type": "Creative Commons Attribution (CC BY)",
            "attribution": "NetworkChuck Docker Tutorial",
            "source_url": "https://www.youtube.com/watch?v=Gjnup-PuquQ",
            "allow_embedding": True,
            "tags": "Docker, DevOps, Containers",
            "facts": [
                "Docker is a platform for developing, shipping, and running applications in containers.",
                "A container is a standard unit of software that packages up code and all its dependencies.",
                "Containers run reliably from one computing environment to another.",
                "Unlike virtual machines, containers do not bundle a full operating system.",
                "Containers share the host system's kernel.",
                "Because they share the kernel, containers are much more lightweight and faster to start than VMs.",
                "A Docker image is a read-only template with instructions for creating a Docker container.",
                "A Docker container is a runnable instance of an image.",
                "You can create, start, stop, move, or delete a container using the Docker API or CLI.",
                "A Dockerfile is a text document that contains all the commands to assemble an image.",
                "The 'docker build' command builds an image from a Dockerfile.",
                "The 'docker run' command creates and starts a container from an image.",
                "The 'docker ps' command lists running containers.",
                "The 'docker images' command lists downloaded or built images.",
                "The 'docker stop' command stops a running container gracefully.",
                "The 'docker rm' command removes a stopped container.",
                "The 'docker rmi' command removes an image.",
                "Docker Hub is a public registry where you can find and share container images.",
                "The 'docker pull' command downloads an image from a registry.",
                "The 'docker push' command uploads an image to a registry.",
                "Docker volumes provide a way to persist data generated by and used by Docker containers.",
                "Volumes are completely managed by Docker.",
                "Bind mounts allow you to map a file or directory on the host machine into a container.",
                "Docker networks allow containers to communicate with each other.",
                "The default network driver for containers is the 'bridge' network.",
                "Docker Compose is a tool for defining and running multi-container Docker applications.",
                "Docker Compose uses a YAML file to configure application services.",
                "The 'docker-compose up' command builds, (re)creates, starts, and attaches to containers for a service.",
                "Containers enforce isolation using Linux namespaces.",
                "Containers restrict resource usage using Linux control groups (cgroups)."
            ]
        },
        {
            "title": "Understanding Git and Version Control",
            "description": "Learn the basics of Git: commits, branches, merges, and resolving conflicts.",
            "module": "Software Engineering",
            "topic": "Version Control",
            "difficulty": "beginner",
            "duration_seconds": 1150,
            "video_url": "https://www.youtube.com/embed/8JJ101D3knE",
            "thumbnail_url": "https://img.youtube.com/vi/8JJ101D3knE/hqdefault.jpg",
            "source_name": "Programming with Mosh",
            "license_type": "External Embed — License Requires Verification",
            "attribution": "Programming with Mosh Git Tutorial",
            "source_url": "https://www.youtube.com/watch?v=8JJ101D3knE",
            "allow_embedding": True,
            "tags": "Git, Version Control, Collaboration",
            "facts": [
                "Git is a distributed version control system.",
                "It tracks changes in any set of files, usually used for coordinating work among programmers.",
                "A repository (repo) is a directory which contains your project work, as well as a few files used to communicate with Git.",
                "The working directory contains the currently checked out version of the files.",
                "The staging area (index) is a file that stores information about what will go into your next commit.",
                "A commit is a snapshot of your repository at a specific point in time.",
                "The 'git init' command initializes a new Git repository.",
                "The 'git clone' command creates a copy of an existing repository.",
                "The 'git status' command shows the state of the working directory and the staging area.",
                "The 'git add' command adds a change in the working directory to the staging area.",
                "The 'git commit' command saves the changes in the staging area to the repository.",
                "Every commit has a unique SHA-1 hash identifier.",
                "A branch represents an independent line of development.",
                "The default branch name in Git is usually 'master' or 'main'.",
                "The 'git branch' command lists, creates, or deletes branches.",
                "The 'git checkout' or 'git switch' command is used to switch from one branch to another.",
                "The 'git merge' command integrates changes from another branch into the current branch.",
                "A merge conflict occurs when Git cannot automatically resolve differences in code between two commits.",
                "The 'git log' command shows the commit history.",
                "A remote repository is a version of your project hosted on the internet or network.",
                "The 'git remote' command manages the set of tracked repositories.",
                "The 'git push' command updates a remote repository with local commits.",
                "The 'git pull' command fetches from and integrates with another repository or a local branch.",
                "The 'git fetch' command downloads objects and refs from another repository without merging.",
                "A .gitignore file specifies intentionally untracked files that Git should ignore.",
                "The 'git stash' command temporarily shelves changes you've made to your working copy.",
                "The 'git rebase' command reapplies commits on top of another base tip.",
                "Rebasing rewrites commit history.",
                "The 'git diff' command shows changes between commits, commit and working tree, etc.",
                "HEAD is a reference to the currently checked out commit."
            ]
        },
        {
            "title": "Convolutional Neural Networks (CNN) for Computer Vision",
            "description": "Learn how convolutions, padding, strides, and pooling layers work in deep learning.",
            "module": "Deep Learning",
            "topic": "Computer Vision",
            "difficulty": "advanced",
            "duration_seconds": 1800,
            "video_url": "https://www.youtube.com/embed/YRhxdVk_sIs",
            "thumbnail_url": "https://img.youtube.com/vi/YRhxdVk_sIs/hqdefault.jpg",
            "source_name": "DeepLearning.AI",
            "license_type": "Creative Commons Attribution (CC BY)",
            "attribution": "DeepLearning.AI CNN Tutorial",
            "source_url": "https://www.youtube.com/watch?v=YRhxdVk_sIs",
            "allow_embedding": True,
            "tags": "Deep Learning, CNN, Computer Vision",
            "facts": [
                "A Convolutional Neural Network (CNN) is a class of artificial neural network commonly used to analyze visual imagery.",
                "CNNs employ a mathematical operation called convolution in place of general matrix multiplication.",
                "The main building block of a CNN is the convolutional layer.",
                "A filter (or kernel) is a small matrix used for feature extraction during convolution.",
                "Filters slide over the input image to produce feature maps (or activation maps).",
                "Stride specifies how many pixels the filter shifts over the input matrix.",
                "Padding involves adding extra pixels around the boundary of the input image.",
                "Valid padding means no padding is added; the spatial dimensions reduce.",
                "Same padding means padding is added so the output has the same spatial dimensions as the input.",
                "Pooling layers are used to reduce the spatial dimensions (width and height) of the input.",
                "Max pooling selects the maximum value from a region of the feature map.",
                "Average pooling calculates the average value of a region.",
                "Pooling helps make the representation approximately invariant to small translations of the input.",
                "Activation functions introduce non-linearities into the network.",
                "ReLU (Rectified Linear Unit) is the most commonly used activation function in CNNs.",
                "ReLU outputs the input if it is positive, and zero otherwise.",
                "Fully Connected (FC) layers connect every neuron in one layer to every neuron in the next layer.",
                "FC layers are typically placed at the end of a CNN for classification.",
                "Flattening is the process of converting a 2D feature map into a 1D vector before feeding it to an FC layer.",
                "Dropout is a regularization technique where randomly selected neurons are ignored during training.",
                "Dropout helps prevent overfitting.",
                "Softmax is often used in the final layer for multi-class classification, outputting a probability distribution.",
                "Cross-entropy loss is commonly used for classification tasks with CNNs.",
                "Data augmentation artificially increases the size of a training dataset by applying transformations (e.g., rotation, flipping).",
                "Transfer learning involves reusing a pre-trained model on a new problem.",
                "VGG, ResNet, and Inception are famous CNN architectures.",
                "ResNet introduced residual blocks with skip connections to train very deep networks.",
                "CNNs are translation invariant due to parameter sharing in convolutional layers.",
                "Parameter sharing means that a feature detector useful in one part of the image is likely useful in another.",
                "Receptive field is the region of the input space that affects a particular CNN feature."
            ]
        }
    ]

    all_data = []

    for v in videos:
        quizzes = []
        difficulties = [
            ("Easy", 15, "beginner"),
            ("Moderate", 10, "intermediate"),
            ("Difficult", 5, "advanced")
        ]
        
        # Facts for this topic (there are 30)
        facts = v['facts']
        
        for q_title, q_count, q_diff in difficulties:
            questions = []
            
            # Select subset of facts based on difficulty
            if q_diff == "beginner":
                subset = facts[0:15]
            elif q_diff == "intermediate":
                subset = facts[15:25]
            else:
                subset = facts[25:30]
                
            for i, fact in enumerate(subset):
                # Build a question out of the fact
                words = fact.split()
                # Dummy options for multiple choice
                correct = fact
                wrong1 = fact.replace(words[min(3, len(words)-1)], "NOT_" + words[min(3, len(words)-1)])
                wrong2 = fact.replace(words[min(5, len(words)-1)], "WRONG_" + words[min(5, len(words)-1)])
                wrong3 = "This statement is generally incorrect regarding the topic."
                
                # Question structure based on difficulty rules
                if q_diff == "beginner":
                    q_text = f"Recall a basic concept about {v['topic']}: Which of the following is true?"
                elif q_diff == "intermediate":
                    q_text = f"Apply your understanding of {v['topic']}: Identify the correct statement."
                else:
                    q_text = f"Reasoning scenario for {v['topic']}: Evaluate the following and select the accurate description."
                
                # Assign to random options (we'll just statically assign for simplicity, rotating correct option)
                correct_opt = ["a", "b", "c", "d"][i % 4]
                opts = {"a": wrong1, "b": wrong2, "c": wrong3, "d": wrong3}
                opts[correct_opt] = correct
                # ensure all are unique strings at least
                opts["c"] = wrong3 + " (A)" if correct_opt != "c" else correct
                opts["d"] = wrong3 + " (B)" if correct_opt != "d" else correct

                questions.append({
                    "question": q_text,
                    "option_a": opts["a"],
                    "option_b": opts["b"],
                    "option_c": opts["c"],
                    "option_d": opts["d"],
                    "correct_option": correct_opt,
                    "explanation": f"The correct answer is based on the principle: {fact}",
                    "difficulty": q_diff,
                    "marks": 1 if q_diff == "beginner" else 2 if q_diff == "intermediate" else 3
                })
                
            quizzes.append({
                "title": f"{v['topic']} - {q_title} Quiz",
                "description": f"Test your understanding with this {q_diff} quiz on {v['topic']}.",
                "module": v['module'],
                "topic": v['topic'],
                "difficulty": q_diff,
                "questions": questions
            })
            
        v['quizzes'] = quizzes
        # Remove facts before saving
        del v['facts']
        all_data.append(v)

    out_path = os.path.join(os.path.dirname(__file__), 'seed_data.json')
    with open(out_path, 'w') as f:
        json.dump(all_data, f, indent=4)
    print(f"Generated seed data at {out_path}")

if __name__ == "__main__":
    generate_seed_data()
