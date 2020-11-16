# moodle_scraper
A moodle scraper API that allows you to browse fmf and fri moodle forums in JSON

API available at [Heroku](https://fmf-fri-moodle-scraper.herokuapp.com/)

Endpoints:
```
  /getDeadlines - returns list of quiz and assignment deadlines
    params:
      location (req.) - select fri or fmf
    returns:
      [
        {id: {due}, ...}, ..., - for assignments
        {id: {open, close}, ...}, ... - for quizzes
      ]

  /getAssignments - get assignments for a subject
    params:
      location (req.) - select fri or fmf
      abbr (optional) - if ommitted, assignments for all subjects are returned
      deadlines (optional - def. false) - include deadlines?
    returns:
       {abbr: [ {title, id, deadline:{due}}}, ... ]}

   /getQuizzes - get quizzes for a subject
     params:
       location (req.) - select fri or fmf
       abbr (optional) - if ommitted, quizzes for all subjects are returned
	   deadlines (optional - def. false) - include deadlines?
     returns:
        {abbr: [ {title, id, deadline:{open, close}}, ... ]}

  /getForumList - get forums for a subject
    params:
      location (required) - select fri or fmf
      abbr (optional) - if ommitted, forums for all subjects are returned
    returns:
       {abbr: [ {title, id}, ... ]}

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
```GET https://fmf-fri-moodle-scraper.herokuapp.com/getQuizzes?location=fri```  
```GET https://fmf-fri-moodle-scraper.herokuapp.com/getForumList?location=fmf&abbr=LINALG```  
```GET https://fmf-fri-moodle-scraper.herokuapp.com/getPosts?location=fri&forum_id=9```  

Environment variables:
* PORT (def. 5000) port on which to listen
* USERNAME moodle username
* PASSWORD moodle password
