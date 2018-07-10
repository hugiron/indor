CREATE OR REPLACE FUNCTION function_update_camera_complete()
  RETURNS TRIGGER AS
$BODY$
BEGIN
  NEW.delay = NEW.last_update - OLD.last_update;
  RETURN NEW;
END;
$BODY$
LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trigger_update_camera_complete ON camera CASCADE;


CREATE TRIGGER trigger_update_camera_complete
  AFTER UPDATE
  ON camera
  FOR EACH ROW
  WHEN (OLD.is_complete = false AND NEW.is_complete = true)
EXECUTE PROCEDURE function_update_camera_complete();
