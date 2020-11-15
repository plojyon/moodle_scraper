# moodle_scraper
A moodle scraper API that allows you to browse fmf and fri moodle forums in JSON

API available at [Heroku](https://fmf-fri-moodle-scraper.herokuapp.com/)

Endpoints:
```
  /getAssignments - get assignments and quizzes for a subject
    params:
      location (req.) - select fri or fmf
      abbr (optional) - if ommitted, assignments for all subjects are returned
    returns:
       {abbr: [ {title, id, type: "assign" | "quiz", subject:{abbr, name}, deadline}, ... ]}

  /getForumList - get forums for a subject
    params:
      location (required) - select fri or fmf
      abbr (optional) - if ommitted, forums for all subjects are returned
    returns:
       {abbr: [ {title, id, subject:{abbr, name}}, ... ]}

  /getForum: - returns posts from given forum
    params:
      location (required) - select fri or fmf
      forum_id (required)
    returns:
      [ {title, id, author, last_submission}, ... ]

  /getPostDetails:
    params:
      location (required) - fri or fmf
      post_id (required)
    returns:
      [
        {
          title,
          author,
          timestamp,
          content,
          replies:{
            title,
            author,
            timestamp,
            content,
            replies:{...}
          }
        },
        ...
      ]
```

Example request:  
```GET https://fmf-fri-moodle-scraper.herokuapp.com/getForums?location=fmf&abbr=LINALG```  
```GET https://fmf-fri-moodle-scraper.herokuapp.com/getPosts?location=fri&forum_id=9```  

Environment variables:
* PORT (def. 5000) port on which to listen
* DEBUG (def. 1) is app in debug mode? Set to 0 for production
* USERNAME moodle username
* PASSWORD moodle password
