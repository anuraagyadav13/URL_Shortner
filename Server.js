import express from 'express'
import mongoose from 'mongoose'
const app = express()
const port = 3000

mongoose.connect(
  'mongodb+srv://anutechx2707:CSbNs9v9QjJYtL2U@cluster0.ockiyc0.mongodb.net/',
  { dbName: 'URL_Shortner' }
).then(() => console.log('MongoDB Connected..!'))
 .catch(err => console.log(err))

app.set('view engine', 'ejs')

app.get('/', (req, res) => {
  res.render('index', { shortUrl: null })
})

app.listen(port, () => console.log(`Server is running on ${port}`))

