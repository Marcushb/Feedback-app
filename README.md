# Backend of the feedback application

## Guide for deploying app locally in docker.
### Prerequisites
Windows:
- install docker desktop
  - preferably setup docker desktop with wsl2 (also install wsl2)
- Install docker-compose

Linux:
- install docker
- install docker-compose

### How to use docker-compose
Deploying feedback-app using docker-compose
1) build image
    - from Feedback-app folder, run: `docker-compose build`
2) run docker-compose
    - from Feedback-app folder, run: `docker-compose up`

In order to shut down app again, run: `docker-compose down`

### Accessing deployed app
Locally deployed app can be found on: `localhost:5050` 

Locally deployed db can be found on:
`localhost: 5432`

Locally deployed pgadmin app can be found on:
`localhost: 82`
login:
- username: see docker-compose variable `PGADMIN_DEFAULT_EMAIL`
- password: see docker-compose variable `PGADMIN_DEFAULT_PASSWORD`

OBS: Internally, `localhost` should be exchanged for the name found in `docker-compose.yaml`.
e.g. to access database from pgadmin, use hostname:
`postgresql-db`

### Accessing DB from pgadmin
1) Log in to pgadmin using details from `docker-compose.yaml`
2) Add server using hostname=`postgresql-db`, port=`5432`. Username and password is found in `docker-compose.yaml`

### How to use docker
In order to deploy the app as a container in docker
1) build image
    - From Feedback-app folder, run: 
      - `docker build -t feedback-app .`
2) run image (can be done in docker, but prefereably done in docker-compose) 
    - `docker run -p 5050:5000 feedback-app`

Useful commands:
- List existing images, running and stopped:
  - `docker ps -a`
- clean up images
  - `docker rmi <image-id>` 
- stop running container
  - `docker stop <container-id>`
- remove container
  - `docker rm <container-id>`


___

# App Documentation

## Documentation for calls

---
<br/>

### **Login with Microsoft**
<br/>

<ins> General information </ins>

>* Route: `/login_microsoft`
>* Methods: `POST`

<ins> Parameters </ins>:

>* accessToken `{string}` `[body]`

<ins> Returns </ins>:

>* jwtToken `{string}`
>* email `{string}`
>* name `{string}`

```
{
    "jwtToken": "andlnawlaw32525kwnlkn.awdawjdo115m.fdnalnfd",
    "email": "example_email@outlook.com",
    "name": "Firstname Lastname"
}
```

<ins> Purpose </ins>:

* A user is logged in to Microsoft by use of the received `accessToken`. If the user
does not already exist in the database, the user is created based on the email and 
name received from Microsoft when logging in. An email is always present, as this is
used to login with, however the name of the user received from Microsoft can be empty.
If this is the case, `None/nill` is returned in the `name`, instead of an empty string.

---
<br/>

### **Get Microsoft events from Outlook calendar**
<br/>

<ins> General information </ins>

>* Route: `/get_microsoft_events`
>* Methods: `POST`

<ins> Parameters: </ins>

>* x-access-token `{string}` `[header]`
>* accessToken `{string}` `[body]`

<ins> Returns: </ins>

* `response` object which for each meeting contains:
>* id `{string}`
>* subject `{string}`
>* bodyPreview `{string}`
>* startTime `{string in ISO 8601 UTC format}`
>* endTime `{string in ISO 8601 UTC format}`
>* location `{string}`
>* attendees `{list of object(s)}`
>   * email `{string}`
>   * name `{string}`

```
{
    "response": [
        {
            "attendees": [
                {
                    "email": "email1@outloook.com",
                    "name": "Firstname1 Lastname1"
                },
                {
                    "email": "email2@outlook.com",
                    "name": "Firstname2 Lastname2"
                }
            ],
            "bodyPreview": "A description of the scheduled meeting",
            "endTime": "2022-01-04T11:30:00Z",
            "id": "AQMkADAwYjQxLTA1L7qaFAoaDaFAJIaTsABQbAAA=",
            "location": "SomePlace",
            "startTime": "2022-01-04T11:00:00Z",
            "subject": "The subject of the meeting"            
        },
        {
            "attendees": [
                {
                    "email": "email1@outloook.com",
                    "name": "Firstname1 Lastname1"
                },
                {
                    "email": "email2@outlook.com",
                    "name": "Firstname2 Lastname2"
                },
                {
                    "email": "email3@outlook.com",
                    "name": "Firstname3 Lastname3"
                },
                {
                    "email": "email4@outlook.com",
                    "name": "Firstname4 Lastname4"
                }
            ],
            "bodyPreview": "A description of the scheduled meeting",
            "endTime": "2022-10-20T11:30:00Z",
            "id": "AQMkADAwYjQxLTA1L7qaFAoaDaFAJIaTsABQbAAA=",
            "location": "SomePlace",
            "startTime": "2022-10-20T11:45:00Z",
            "subject": "The subject of the meeting"            
        }
    ]
}
```


<ins> Purpose: </ins>

* The events of a users Outlook calendar is fetched from Microsoft. If the `accessToken`
used to log in to Microsoft has expired, an error corresponding to the received Microsoft
error will be returned. 

---
<br/>

### **Create event**
<br/>

<ins> General information </ins>

>* Route: `/create_event`
>* Methods: `POST`

<ins> Parameters: </ins>

>* x-access-token `{string}` `[header]`
>* title `{string}` `[body]` `(required)`
>* startDate `{string}` `[body]` `(required)`
>* endDate `{string}` `[body]` `(required)`
>* description `{string}` `[body]` 
>* questions `{list of strings}` `[body]`

<ins> Returns: </ins>

* Nothing (empty object)
```
{}
```


<ins> Purpose: </ins>

* A logged in user can create an event with the parameters described above. A unique pin
will be added to the event, while it remains active. This pin can be used by other
non-logged-in users, to give feedback on the questions asked by the creator of the event.
See [submit_feedback](Placeholder) ##FUNCTIONALITY YET TO BE IMPLEMENTED.

---
<br/>

### **Modify or delete an event**
<br/>

<ins> General information </ins>

>* Route: `/modify_event`
>* Methods: `PUT, DELETE`

<br/>

If Method is <ins>__PUT__ </ins>:

<ins> Parameters </ins>:

>* x-access-token `{string}` `[header]` `(required)`
>* ID `{integer}` `[body]` `(required)`
>* title `{string}` `[body]`
>* startDate `{string}` `[body]`
>* endDate `{string}` `[body]`
>* description `{string}` `[body]`

<ins> Returns </ins>:

>* Nothing (empty object)
```
{}
```

<br/>

<ins> Purpose </ins>:

* Given the `ID` of an existing event, this allows the owner of the event to change the 
contents of said event.
Parameters available to be changed/overwritten, as listed above, are:
    * `title`
    * `startDate`
    * `endDate`
    * `description`

<br/>

If Method is <ins>__DELETE__ </ins>:

<ins> Parameters </ins>:

>* x-access-token `{string}` `[header]` `(required)`
>* ID `{list of integer(s)}` `[body]` `(required)`

<ins> Returns </ins>:

>* Nothing (empty object)
```
{}
```

<ins> Purpose </ins>:

* Given the `ID(s)` of an existing event, this allows the owner of an event to delete the
event(s) corresponding to the `ID(s)`, along with every question and given feedback 
associated with the event(s).


---
<br/>

### **Modify or delete a question**
<br/>

<ins> General information </ins>

>* Route: `/modify_question`
>* Methods: `PUT, DELETE`

<br/>

If Method is <ins>__PUT__ </ins>:

<ins> Parameters </ins>:

>* x-access-token `{string}` `[header]` `(required)`
>* ID `{integer}` `[body]` `(required)`
>* description `{string}` `[body]`

<ins> Returns </ins>:

>* Nothing (empty object)
```
{}
```

<br/>

<ins> Purpose </ins>:

* Given the `ID` of an existing question belonging to an event, this allows the owner of 
the event to change the description of the question.
Parameter available to be changed/overwritten, as listed above, are:
    * `description`

<br/>

If Method is <ins>__DELETE__ </ins>:

<ins> Parameters </ins>:

>* x-access-token `{string}` `[header]` `(required)`
>* ID `{list of integer(s)}` `[body]` `(required)`

<ins> Returns </ins>:

>* Nothing (empty object)
```
{}
```

<ins> Purpose </ins>:

* Given the `ID(s)` of existing question(s), this allows the owner of an event to delete 
the question(s) corresponding to the `ID(s)`, along with all given feedback 
associated with the question(s).

---


### **Get events**
<br/>

<ins> General information </ins>

>* Route: `/events`
>* Methods: `GET`

<ins> Parameters: </ins>

>* x-access-token `{string}` `[header]`

<ins> Returns: </ins>

* `response` object which for each event contains:
>* id `{integer}`
>* title `{string}`
>* startDate `{string}`
>* endDate `{string}`
>* feedbackCount `{integer}`
>* rating1 `{integer}`
>* rating2 `{integer}`
>* rating3 `{integer}`
>* rating4 `{integer}`
>* isActive `{logical}`

```
{
    "response": [
        {
            "id": 1,
            "title": "Title of event",
            "startDate": "2022-01-04T11:30:00Z",
            "endDate": "2022-01-04T11:45:00Z",
            "feedbackCount": "10",
            "rating1": 1,
            "rating2": 1,
            "rating3": 4,
            "rating4": 2,
            "isActive": True
        },
        {
            "id": 12,
            "title": "Title of another event",
            "startDate": "2022-12-05T07:50:00Z",
            "endDate": "2022-12-05T08:00:00Z",
            "feedbackCount": "5",
            "rating1": 0,
            "rating2": 0,
            "rating3": 2,
            "rating4": 3,
            "isActive": False
        },
    ]
}
```


<ins> Purpose: </ins>

* Returns information of all events a user has created. This is used to display general
event information on the home screen of the user, showing general information about the
event. This includes a count of the amount of received feedback on all questions the event contains, as well as some general information about the distribution of the ratings.


---
<br/>



### **Get specific event**
<br/>

<ins> General information </ins>

>* Route: `/events/<id>`
>* Methods: `GET`

<ins> Parameters: </ins>

>* x-access-token `{string}` `[header]`
>* id `{integer}` `[url]`

<ins> Returns: </ins>

* `response` object which contains:
>* title `{string}`
>* startDate `{string}`
>* endDate `{string}`
>* description `{string}`
>* isActive `{logical}`
>* questions `{list of strings}`
>    * rating
>    * content

```
{
    "response": [
        {
            "title": "Title of event",
            "startDate": "2022-01-04T11:30:00Z",
            "endDate": "2022-01-04T11:45:00Z",
            "description": "description of event",
            "isActive": True,
            "questions": [
                {
                    "question": "What did you think of the event overall?",
                    "feedbacks": [
                        {
                            "rating": 4,
                            "content": "Event was very informative on the subject"
                        },
                        {
                            "rating": 3,
                            "content": "Solid event, however more in-depth analysis would have elevated it"
                        }
                    ]
                },
                                {
                    "question": "Did the presenter involve the audicence?",
                    "feedbacks": [
                        {
                            "rating": 3,
                            "content": "The presenter was made sure, that..."
                        },
                        {
                            "rating": 2,
                            "content": "I did not personally feel a strong engagement"
                        }
                    ]
                }
            ]
        },
            "title": "Title of event2",
            "startDate": "2022-01-04T11:30:00Z",
            "endDate": "2022-01-04T11:45:00Z",
            "description": "description of event2",
            "isActive": False,
            "questions": []
        },
    ]
}
```


<ins> Purpose: </ins>

* Returns all information of a specific event. This includes all questions related to the
event, as well as all feedback related to each individual question.


---
<br/>