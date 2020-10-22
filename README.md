# moodle_scraper
A moodle scraper API that allows you to browse fmf and fri moodle forums in JSON

Endpoints:
```
  /getForums
    params:
      location (required) - select fri or fmf
      abbr (optional) - only return forums for given subject
    returns:
      [ {title, subject:{abbr, name}, id}, ... ]
  /getPosts:
    params:
      location (required) - select fri or fmf
      forum_id (required) - returns posts from given forum
    returns:
      [ {title, author, timestamp (last submission), id}, ... ]
  /getPostDetails:
    params:
      location (required)
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
