import shortid from 'shortid';
import { Url } from '../Models/Url.js';

export const shortUrl = async (req, res) => {
    try {
        const longUrl = req.body.LongUrl;

        if (!longUrl) {
            return res.status(400).send('URL is required');
        }

        let url = await Url.findOne({ longUrl });

        if (url) {
            return res.render('index', {
                shortUrl: `http://${req.headers.host}/${url.shortCode}`
            });
        }

        const shortCode = shortid.generate();
        url = new Url({ longUrl, shortCode });
        await url.save();

        res.render('index', {
            shortUrl: `http://${req.headers.host}/${shortCode}`
        });
    } catch (error) {
        console.error('Error:', error);
        res.status(500).send('Server Error');
    }
};

export const getOriginalUrl = async (req, res) => {
    try {
        const { shortCode } = req.params;
        const url = await Url.findOne({ shortCode });

        if (!url) {
            return res.status(404).send('URL not found');
        }

        res.redirect(url.longUrl);
    } catch (error) {
        console.error('Error:', error);
        res.status(500).send('Server Error');
    }
};