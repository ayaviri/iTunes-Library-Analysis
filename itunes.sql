-- database creation
drop database if exists itunes;
create database itunes;

use itunes;

-- table creation
create table song 
(
    Name varchar(64) not null, 
    Artist varchar(64) not null, 
    Kind varchar(64) not null, -- the audio file format
    Total_Time int not null, -- the duration of the audio file in milliseconds
    Year int not null, 
	Date_Added timestamp not null, -- the date of the song's addition to the library
    Play_Count int not null,
    Persistent_ID varchar(64) primary key,
    Current_Upload_Date timestamp not null, -- the date of the current upload to the database
    -- fields not obtained from xml file
    Last_Upload_Date timestamp not null, -- the date of the last upload to the database
    Relative_Play_Count int not null -- the number of plays in between lastUpload and currentUpload
);

select * from song;
select Name, Artist, Relative_Play_Count from song order by Relative_Play_Count desc limit 5;
select Artist, sum(Relative_Play_Count) from song group by Artist;
select Name, Artist, Play_Count from song order by Play_Count desc limit 5;